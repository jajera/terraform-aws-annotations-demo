/** Human-readable labels for GeoNet volcano camera IDs used in this demo. */
export const CAMERA_LABELS = {
  'TKAH.01': 'Te Kaha',
};

export function formatCameraLabel(cameraId) {
  const site = CAMERA_LABELS[cameraId];
  if (!site) return cameraId;
  return `${site} (${cameraId})`;
}
