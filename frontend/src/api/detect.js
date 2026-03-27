// frontend/src/api/detect.js
import axios from "axios";

/**
 * Base URL for the FastAPI backend.
 * During development Vite proxies /api → localhost:8000 (see vite.config.js).
 * In production replace with your deployed API URL via VITE_API_URL env var.
 */
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000, // 30 s — model inference can be slow on CPU
});

/**
 * detectDisease
 * Sends a plant leaf image to POST /api/v1/predict.
 *
 * @param {File} imageFile  — the File object from the file input / drop zone
 * @returns {Promise<{
 *   disease: string,
 *   confidence: number,
 *   symptoms: string,
 *   cure: string
 * }>}
 * @throws {Error} with a user-friendly message on HTTP or network errors
 */
export async function detectDisease(imageFile) {
  const formData = new FormData();
  formData.append("file", imageFile);

  try {
    const { data } = await apiClient.post("/api/v1/predict", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  } catch (err) {
    // Axios wraps HTTP errors in err.response
    if (err.response) {
      const detail = err.response.data?.detail;
      throw new Error(
        detail ||
          `Server returned ${err.response.status}. Please try again.`
      );
    }

    // Network / timeout
    if (err.code === "ECONNABORTED") {
      throw new Error(
        "Request timed out. The server may be busy — please try again."
      );
    }

    throw new Error(
      "Could not reach the server. Make sure the backend is running."
    );
  }
}