"""Video playback thread with frame queue and optimization."""
import logging
import queue
import threading
import time
from typing import Any, Callable, Dict, Optional
import cv2
import numpy as np

from .config import PerformanceConfig

logger: logging.Logger = logging.getLogger(__name__)

_ffmpeg_lock: threading.Lock = threading.Lock()


class VideoPlayerThread:
    """Thread for playing a single video and providing frames."""
    
    def __init__(
        self,
        video_data: Dict[str, Any],
        fps_getter: Callable[[], int],
        optimize_getter: Callable[[], bool],
        settings: Dict[str, Any],
        video_index: int,
    ) -> None:
        """Initialize video player thread."""
        self._video_data: Dict[str, Any] = video_data
        self._fps_getter: Callable[[], int] = fps_getter
        self._optimize_getter: Callable[[], bool] = optimize_getter
        self._settings: Dict[str, Any] = settings
        self._video_index: int = video_index
        
        self._is_playing: threading.Event = threading.Event()
        self._is_paused: threading.Event = threading.Event()
        self._stop_event: threading.Event = threading.Event()
        
        self._frame_queue: queue.Queue = queue.Queue(
            maxsize=settings.get('queue_size', PerformanceConfig.FRAME_QUEUE_SIZE)
        )
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None
        self._last_frame_time: float = 0.0
        self._current_frame_pos: int = 0
        self._video_aspect_ratio: float = 1.0
        self._thread_exited: threading.Event = threading.Event()

    def start(self) -> None:
        """Start video playback thread."""
        self._is_playing.set()
        self._is_paused.clear()
        self._stop_event.clear()
        self._thread_exited.clear()
        self._thread = threading.Thread(target=self._play_loop, daemon=True)
        self._thread.start()
        logger.debug(f"Started video thread {self._video_index}")

    def stop(self) -> None:
        """Stop video playback immediately."""
        self._stop_event.set()
        self._is_playing.clear()
        
        if self._cap is not None:
            try:
                self._cap.release()
                self._cap = None
            except cv2.error as e:
                logger.warning(f"Error releasing video capture: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error releasing capture: {e}")
        
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break

    def wait_for_exit(self, timeout: float = PerformanceConfig.THREAD_EXIT_TIMEOUT) -> bool:
        """Wait for thread to exit with timeout."""
        return self._thread_exited.wait(timeout=timeout)

    def pause(self) -> None:
        """Pause video playback."""
        self._is_paused.set()
        if self._cap is not None:
            try:
                self._current_frame_pos = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
            except cv2.error:
                pass
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)

    def resume(self) -> None:
        """Resume video playback."""
        self._is_paused.clear()

    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame from the queue."""
        try:
            return self._frame_queue.get_nowait()
        except queue.Empty:
            return None

    def _get_video_capture(self, path: str) -> Optional[cv2.VideoCapture]:
        """Create a VideoCapture with the selected backend."""
        backend: str = self._settings.get('backend', 'AUTO')
        
        try:
            if backend == 'FFMPEG':
                with _ffmpeg_lock:
                    cap: cv2.VideoCapture = cv2.VideoCapture(path, cv2.CAP_FFMPEG)
            elif backend == 'MSMF':
                cap = cv2.VideoCapture(path, cv2.CAP_MSMF)
            elif backend == 'DSHOW':
                cap = cv2.VideoCapture(path, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(path)
            
            if cap is not None and cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return cap
        except cv2.error as e:
            logger.error(f"OpenCV error opening video {path}: {e}")
        except Exception as e:
            logger.error(f"Error opening video {path}: {e}")
        
        return None

    def _play_loop(self) -> None:
        """Main playback loop running in background thread."""
        try:
            # No delay - instant start for speed
            self._cap = self._get_video_capture(self._video_data['path'])
            if self._cap is None or not self._cap.isOpened():
                self._video_data['valid'] = False
                logger.warning(f"Could not open video: {self._video_data['path']}")
                self._thread_exited.set()
                return
            
            width: float = self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height: float = self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            if width > 0 and height > 0:
                self._video_aspect_ratio = width / height
                self._video_data['aspect_ratio'] = self._video_aspect_ratio
            else:
                self._video_aspect_ratio = 16 / 9
            
            fps: float = self._cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30.0
            
            if self._current_frame_pos > 0:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, self._current_frame_pos)
            
            frame_skip_counter: int = 0
            consecutive_failures: int = 0
            
            while True:
                if self._stop_event.is_set():
                    break
                
                if not self._is_playing.is_set():
                    break
                
                if self._is_paused.is_set():
                    time.sleep(PerformanceConfig.THREAD_PAUSE_SLEEP)
                    continue
                
                current_time: float = time.time()
                target_fps: int = min(int(fps), self._fps_getter())
                frame_time: float = 1.0 / target_fps if target_fps > 0 else 0.033
                
                # Optimized timing - only sleep if needed
                elapsed: float = current_time - self._last_frame_time
                if elapsed < frame_time:
                    sleep_time: float = frame_time - elapsed
                    if sleep_time > 0.005:
                        time.sleep(sleep_time)
                    continue
                
                ret: bool
                frame: Optional[np.ndarray]
                ret, frame = self._cap.read()
                
                if not ret or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures > PerformanceConfig.THREAD_READ_RETRY:
                        if self._cap is not None:
                            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            ret, frame = self._cap.read()
                            if not ret or frame is None:
                                self._is_playing.clear()
                                break
                        else:
                            break
                    else:
                        time.sleep(0.001)
                        continue
                    consecutive_failures = 0
                
                # Optimization: frame skipping
                if self._optimize_getter() and self._settings.get('skip_frames', True):
                    threshold: int = self._settings.get(
                        'optimize_threshold', 
                        PerformanceConfig.OPTIMIZE_THRESHOLD_DEFAULT
                    )
                    videos_count: int = len(self._video_data.get('videos', []))
                    skip_rate: int = max(1, videos_count // threshold) if videos_count > 0 else 1
                    frame_skip_counter = (frame_skip_counter + 1) % skip_rate
                    if frame_skip_counter != 0:
                        self._last_frame_time = current_time
                        continue
                
                frame = self._resize_frame(frame)
                if frame is not None:
                    self._queue_frame(frame)
                
                self._last_frame_time = current_time
                    
        except cv2.error as e:
            logger.error(f"OpenCV error in playback loop: {e}")
        except Exception as e:
            logger.error(f"Error in playback loop: {e}")
        finally:
            if self._cap is not None:
                try:
                    self._cap.release()
                except cv2.error:
                    pass
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)
                self._cap = None
            self._thread_exited.set()

    def _resize_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Resize frame to fit the target cell."""
        cell_w: int = self._video_data['width']
        cell_h: int = self._video_data['height']
        
        if cell_w <= 0 or cell_h <= 0:
            return None
        
        h: int
        w: int
        h, w = frame.shape[:2]
        if h == 0 or w == 0:
            return None
            
        video_ratio: float = w / h
        cell_ratio: float = cell_w / cell_h
        
        if video_ratio > cell_ratio:
            new_w: int = cell_w
            new_h: int = int(cell_w / video_ratio)
        else:
            new_h = cell_h
            new_w = int(cell_h * video_ratio)
        
        new_w = max(1, new_w)
        new_h = max(1, new_h)
        
        quality: str = self._settings.get('resize_quality', 'Medium')
        interpolation: int
        if 'Low' in quality:
            interpolation = cv2.INTER_NEAREST
        elif 'High' in quality:
            interpolation = cv2.INTER_LANCZOS4
        else:
            interpolation = cv2.INTER_LINEAR
        
        try:
            frame = cv2.resize(frame, (new_w, new_h), interpolation=interpolation)
            
            result: np.ndarray = np.zeros((cell_h, cell_w, 3), dtype=np.uint8)
            x_offset: int = (cell_w - new_w) // 2
            y_offset: int = (cell_h - new_h) // 2
            
            if x_offset >= 0 and y_offset >= 0:
                end_x: int = min(x_offset + new_w, cell_w)
                end_y: int = min(y_offset + new_h, cell_h)
                result[y_offset:end_y, x_offset:end_x] = frame[:end_y - y_offset, :end_x - x_offset]
            
            return cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        except cv2.error as e:
            logger.error(f"Error resizing frame: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error resizing: {e}")
            return None

    def _queue_frame(self, frame: np.ndarray) -> None:
        """Add frame to queue, dropping old frames if necessary."""
        try:
            if self._frame_queue.full():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self._frame_queue.put(frame, block=False)
        except queue.Full:
            pass
        except Exception as e:
            logger.debug(f"Error queueing frame: {e}")