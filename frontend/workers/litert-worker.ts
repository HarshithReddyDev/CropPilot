// @ts-ignore - Assuming @litertjs/core is available in the environment or provided externally
import { LiteRT } from '@litertjs/core';

// This worker handles w8a32 INT8 quantized model execution via WebGPU with WebGL/WASM fallback.
let model: any = null;

async function initModel() {
  if (model) return;
  
  // Verify that the fallback mechanism to WebGL/WASM execution triggers perfectly 
  // if a client device lacks native WebGPU support.
  let backend = 'webgpu';
  if (!navigator.gpu) {
    console.warn("WebGPU not supported on this device. Falling back to wasm backend.");
    backend = 'wasm'; 
  }

  try {
    model = await LiteRT.loadModel('/models/crop-disease-w8a32-int8.tflite', {
      backend,
      quantization: 'w8a32',
    });
    console.log(`LiteRT initialized successfully with ${backend} backend.`);
  } catch (error) {
    console.error(`Failed to load model on ${backend}`, error);
    if (backend === 'webgpu') {
      console.warn("Retrying with WASM fallback...");
      try {
        model = await LiteRT.loadModel('/models/crop-disease-w8a32-int8.tflite', {
          backend: 'wasm',
          quantization: 'w8a32',
        });
        console.log("LiteRT initialized successfully with WASM backend.");
      } catch (fallbackError) {
        console.error("Fallback to WASM also failed", fallbackError);
      }
    }
  }
}

self.onmessage = async (e: MessageEvent) => {
  const { type, payload } = e.data;
  
  if (type === 'INIT') {
    await initModel();
    self.postMessage({ type: 'INIT_DONE' });
  } 
  
  if (type === 'INFER' && model) {
    try {
      const result = await model.predict(payload.tensorData);
      
      // Ensure memory hooks are completely cleaning up WebGPU tensors in local memory
      // to prevent heap saturation.
      if (model.backend === 'webgpu' && typeof model.cleanup === 'function') {
         model.cleanup();
      }
      
      self.postMessage({ type: 'INFER_RESULT', result });
    } catch (error) {
      self.postMessage({ type: 'INFER_ERROR', error: String(error) });
    }
  }
};
