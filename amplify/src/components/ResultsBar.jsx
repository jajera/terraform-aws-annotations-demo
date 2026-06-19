import Pagination from './Pagination';

function ResultsBar({
  total,
  offset,
  pageSize,
  showingCount,
  onPageChange,
  disabled,
}) {
  if (total === 0) {
    return null;
  }

  const rangeStart = offset + 1;
  const rangeEnd = offset + showingCount;
  const singlePage = total <= pageSize;

  return (
    <div className="results-bar">
      <p className="results-summary" aria-live="polite">
        <strong>{total}</strong> image{total === 1 ? '' : 's'} match
        {singlePage ? (
          <> — showing all</>
        ) : (
          <> — showing {rangeStart}–{rangeEnd}</>
        )}
      </p>
      <Pagination
        offset={offset}
        pageSize={pageSize}
        total={total}
        onPageChange={onPageChange}
        disabled={disabled}
      />
    </div>
  );
}

export default ResultsBar;
