from core.config import settings


class DiseaseDetectionService:
    def __init__(self):
        self.model = None

    def load_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(settings.YOLO_MODEL_PATH)
        except Exception as e:
            print(f"YOLO model not loaded: {e}")
            self.model = None

    async def detect(self, image_bytes: bytes) -> list[dict]:
        if self.model is None:
            self.load_model()
        if self.model is None:
            return [{"class_name": "unknown", "confidence": 0.0, "bbox": None}]

        import cv2
        import numpy as np

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = self.model(img, conf=settings.CONFIDENCE_THRESHOLD)

        detections = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = result.names[class_id] if class_id in result.names else "unknown"
                detections.append({
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                })

        return detections


disease_detection_service = DiseaseDetectionService()
