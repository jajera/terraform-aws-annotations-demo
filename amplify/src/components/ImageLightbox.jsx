import { useEffect } from 'react';
import TagChips from './TagChips';
import './ImageLightbox.css';

function ImageLightbox({ item, onClose }) {
  const { tags, image_url } = item;
  const altText = `${tags.camera_id || 'camera'} ${tags.captured_utc || ''}`.trim();

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        onClose();
      }
    }

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  return (
    <div
      className="lightbox"
      role="dialog"
      aria-modal="true"
      aria-label="Expanded image view"
      onClick={onClose}
    >
      <div className="lightbox__panel" onClick={(event) => event.stopPropagation()}>
        <button
          type="button"
          className="lightbox__close"
          onClick={onClose}
          aria-label="Close expanded image"
        >
          ×
        </button>
        <img className="lightbox__image" src={image_url} alt={altText} />
        <div className="lightbox__meta">
          <time dateTime={tags.captured_utc}>{tags.captured_utc}</time>
          <TagChips tags={tags} />
        </div>
      </div>
    </div>
  );
}

export default ImageLightbox;
