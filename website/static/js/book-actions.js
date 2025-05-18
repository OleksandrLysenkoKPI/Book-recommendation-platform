function toggleFavourite(bookId) {
  fetch(`/book/${bookId}/toggle_favourite`, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(res => res.json())
  .then(data => {
    const icon = document.querySelector(`#fav-btn-${bookId} i`);
    if (icon) {
      icon.classList.toggle('bi-heart');
      icon.classList.toggle('bi-heart-fill');
    }
  });
}

function toggleRead(bookId) {
  fetch(`/book/${bookId}/toggle_read`, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(res => res.json())
  .then(data => {
    const icon = document.querySelector(`#read-btn-${bookId} i`);
    if (icon) {
      icon.classList.toggle('bi-book');
      icon.classList.toggle('bi-book-fill');
    }
  });
}
