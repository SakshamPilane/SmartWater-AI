// src/utils/getHubImage.js

/**
 * Dynamically loads the correct image for a dam/hub based on its code.
 * Supports multiple file formats and provides a safe fallback image.
 *
 * Example usage:
 *    import getHubImage from "../utils/getHubImage";
 *    <img src={getHubImage("HUB001")} alt="Hub 001" />
 */

const getHubImage = (hubCode) => {
  // Supported image extensions
  const extensions = ["jpg", "jpeg", "png", "webp", "avif"];

  // Try loading each format until one works
  for (const ext of extensions) {
    try {
      return require(`../assets/hubs/${hubCode}.${ext}`);
    } catch (error) {
      // Continue to next format if file not found
    }
  }

  // If no image found, return a default fallback
  try {
    return require(`../assets/hubs/default.jpg`);
  } catch (error) {
    console.warn("⚠️ Default dam image missing in /assets/hubs/default.jpg");
    return ""; // empty string to avoid crash
  }
};

export default getHubImage;
