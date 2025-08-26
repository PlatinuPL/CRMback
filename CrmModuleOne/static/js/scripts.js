// document.addEventListener("DOMContentLoaded", function () {
//   const readMoreLinks = document.querySelectorAll(".read-more");

//   readMoreLinks.forEach((link) => {
//     link.addEventListener("click", function (e) {
//       e.preventDefault();
//       const content = this.previousElementSibling; // Poprzedni element (treść posta)
//       content.style.maxHeight = "none"; // Rozwija treść
//       this.style.display = "none"; // Ukrywa link "Rozwiń"
//     });
//   });
// });
const csrfToken = "{{ csrf_token }}";

document.addEventListener("DOMContentLoaded", function () {
  const checkboxes = document.querySelectorAll(".acknowledge-checkbox");

  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      const postId = this.dataset.postId; // Pobierz post_id
      const url = this.dataset.url; // Pobierz URL z atrybutu data-url
      const isChecked = this.checked; // Sprawdź, czy checkbox jest zaznaczony
      const parentElement = this.closest(".mainNews, .otherNews"); // Znajdź element nadrzędny

      // Wyślij żądanie AJAX
      fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrfToken, // Poprawne użycie tokena CSRF
        },
        body: new URLSearchParams({
          post_id: postId,
        }),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Błąd w żądaniu");
          }
          return response.json();
        })
        .then((data) => {
          if (data.status === "added") {
            console.log(`Post ${data.post_id} został potwierdzony.`);
            this.classList.add("confirmed"); // Dodaj klasę "confirmed"
            if (parentElement) {
              parentElement.classList.remove("unread"); // Usuń klasę "unread"
            }
          } else if (data.status === "removed") {
            console.log(
              `Potwierdzenie dla postu ${data.post_id} zostało usunięte.`
            );
            this.classList.remove("confirmed"); // Usuń klasę "confirmed"
            if (parentElement) {
              parentElement.classList.add("unread"); // Dodaj klasę "unread"
            }
          }
        })
        .catch((error) => {
          console.error("Błąd podczas aktualizacji statusu:", error);
          this.checked = !isChecked; // Przywróć poprzedni stan w razie błędu
        });
    });
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.querySelector(".notification-toggle");
  const dropdown = document.querySelector(".notification-dropdown");

  // Kliknięcie na przycisk Profil
  toggle.addEventListener("click", function (e) {
    e.preventDefault(); // Zapobiega przeładowaniu strony
    dropdown.classList.toggle("show"); // Przełącz widoczność menu
  });

  // Ukrywanie menu po kliknięciu poza nim
  document.addEventListener("click", function (e) {
    if (!dropdown.contains(e.target) && !toggle.contains(e.target)) {
      dropdown.classList.remove("show"); // Ukryj menu
    }
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.querySelector(".profile-toggle");
  const dropdown = document.querySelector(".profile-dropdown");

  // Kliknięcie na przycisk Profil
  toggle.addEventListener("click", function (e) {
    e.preventDefault(); // Zapobiega przeładowaniu strony
    dropdown.classList.toggle("show"); // Przełącz widoczność menu
  });

  // Ukrywanie menu po kliknięciu poza nim
  document.addEventListener("click", function (e) {
    if (!dropdown.contains(e.target) && !toggle.contains(e.target)) {
      dropdown.classList.remove("show"); // Ukryj menu
    }
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const toggles = document.querySelectorAll(".toggle-section");

  toggles.forEach((toggle) => {
    toggle.addEventListener("click", function () {
      const parent = this.parentElement;
      parent.classList.toggle("open"); // Dodaj lub usuń klasę "open"
    });
  });
});




  