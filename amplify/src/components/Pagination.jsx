function Pagination({ offset, pageSize, total, onPageChange, disabled }) {
  if (total <= pageSize) {
    return null;
  }

  const currentPage = Math.floor(offset / pageSize) + 1;
  const totalPages = Math.ceil(total / pageSize);
  const rangeStart = offset + 1;
  const rangeEnd = Math.min(offset + pageSize, total);

  return (
    <nav className="pagination" aria-label="Image results pages">
      <button
        type="button"
        className="pagination__btn"
        onClick={() => onPageChange(currentPage - 2)}
        disabled={disabled || currentPage <= 1}
      >
        Previous
      </button>
      <span className="pagination__status">
        Page {currentPage} of {totalPages}
        <span className="pagination__range">
          ({rangeStart}–{rangeEnd} of {total})
        </span>
      </span>
      <button
        type="button"
        className="pagination__btn"
        onClick={() => onPageChange(currentPage)}
        disabled={disabled || currentPage >= totalPages}
      >
        Next
      </button>
    </nav>
  );
}

export default Pagination;
