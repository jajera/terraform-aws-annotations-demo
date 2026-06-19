import './LoadingSkeleton.css';

function LoadingSkeleton({ count = 8 }) {
  return (
    <section className="image-grid loading-skeleton" aria-label="Loading images" aria-busy="true">
      {Array.from({ length: count }, (_, index) => (
        <article key={index} className="skeleton-card">
          <div className="skeleton-card__thumbnail" />
          <div className="skeleton-card__line skeleton-card__line--short" />
          <div className="skeleton-card__chips">
            <span className="skeleton-card__chip" />
            <span className="skeleton-card__chip" />
            <span className="skeleton-card__chip" />
          </div>
        </article>
      ))}
    </section>
  );
}

export default LoadingSkeleton;
