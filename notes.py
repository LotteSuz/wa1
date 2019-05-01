SELECT review FROM reviews JOIN books ON books.isbn = reviews.isbn;


    for (i = 0; i < tr.length; i++) {
      a = tr[i].getElementsByTagName("tr")[0];
      txtValue = a.textContent || a.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
