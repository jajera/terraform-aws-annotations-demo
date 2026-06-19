import { formatCameraLabel } from '../constants/cameras';

function TagChips({ tags }) {
  return (
    <div className="image-card__chips" aria-label="Image tags">
      {tags.camera_id && (
        <span className="chip chip--category-camera" title={formatCameraLabel(tags.camera_id)}>
          <strong>Camera:</strong> {formatCameraLabel(tags.camera_id)}
        </span>
      )}
      {tags.utc_day && (
        <span className="chip chip--category-day-id">
          <strong>UTC day:</strong> {tags.utc_day}
        </span>
      )}
      {tags.day_phase && (
        <span className="chip chip--category-day">
          <strong>Day:</strong> {tags.day_phase}
        </span>
      )}
      {tags.visibility && (
        <span className={`chip chip--category-visibility chip--visibility-${tags.visibility}`}>
          <strong>Visibility:</strong> {tags.visibility.replace(/_/g, ' ')}
        </span>
      )}
    </div>
  );
}

export default TagChips;
