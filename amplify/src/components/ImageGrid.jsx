import { useState } from 'react';
import TagChips from './TagChips';
import ImageLightbox from './ImageLightbox';
import './ImageGrid.css';

function ImageCard({ item, onExpand }) {
  const [imgError, setImgError] = useState(false);
  const [imgLoaded, setImgLoaded] = useState(false);
  const { tags, image_url } = item;

  const altText = `${tags.camera_id || 'camera'} ${tags.captured_utc || ''}`.trim();
  const displayTimestamp = tags.captured_utc
    ? new Date(tags.captured_utc).toLocaleString(undefined, { hour12: false, timeZone: 'UTC' }) + ' UTC'
    : 'Unknown capture time';

  return (
    <article className="image-card">
      <button
        type="button"
        className="image-card__thumbnail"
        onClick={() => onExpand(item)}
        aria-label={`View full image: ${altText}`}
      >
        {!imgLoaded && !imgError && (
          <div className="image-card__thumbnail-skeleton" aria-hidden="true" />
        )}
        {imgError ? (
          <div className="image-card__placeholder" aria-label="Image unavailable">
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              aria-hidden="true"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <line x1="3" y1="3" x2="21" y2="21" />
            </svg>
            <span>Image unavailable</span>
          </div>
        ) : (
          <img
            src={image_url}
            alt={altText}
            onError={() => setImgError(true)}
            onLoad={() => setImgLoaded(true)}
            loading="lazy"
            decoding="async"
            fetchPriority="low"
            className={imgLoaded ? 'image-card__img--loaded' : 'image-card__img--loading'}
          />
        )}
      </button>

      <div className="image-card__body">
        <time className="image-card__timestamp" dateTime={tags.captured_utc}>
          {displayTimestamp}
        </time>
        <TagChips tags={tags} />
      </div>
    </article>
  );
}

function ImageGrid({ images }) {
  const [expandedItem, setExpandedItem] = useState(null);

  if (!images || images.length === 0) {
    return null;
  }

  return (
    <>
      <section className="image-grid" aria-label="Volcano camera images">
        {images.map((item) => (
          <ImageCard key={item.key} item={item} onExpand={setExpandedItem} />
        ))}
      </section>
      {expandedItem && (
        <ImageLightbox item={expandedItem} onClose={() => setExpandedItem(null)} />
      )}
    </>
  );
}

export default ImageGrid;
