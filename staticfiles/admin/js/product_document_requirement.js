document.addEventListener("DOMContentLoaded", function () {
    const documentSelect = document.getElementById("id_document");
    const placeholderField = document.getElementById("id_required_placeholders");

    function updatePlaceholders() {
        let selectedDocId = documentSelect.value;
        if (!selectedDocId) return;

        fetch(`/admin/CrmModuleOne/productdocumentrequirement/get_placeholders/?document_id=${selectedDocId}`)
            .then(response => response.json())
            .then(data => {
                if (data.placeholders) {
                    let previousSelections = new Set(Array.from(placeholderField.querySelectorAll("input:checked")).map(input => input.value));

                    placeholderField.innerHTML = ""; // Czyszczenie listy

                    data.placeholders.forEach(placeholder => {
                        let label = document.createElement("label");
                        label.style.display = "block";

                        let checkbox = document.createElement("input");
                        checkbox.type = "checkbox";
                        checkbox.value = placeholder;
                        checkbox.name = "required_placeholders";
                        
                        if (previousSelections.has(placeholder)) {
                            checkbox.checked = true; // Zachowanie poprzednich wyborów
                        }

                        label.appendChild(checkbox);
                        label.appendChild(document.createTextNode(" " + placeholder));
                        placeholderField.appendChild(label);
                    });
                }
            })
            .catch(error => console.error("Błąd podczas ładowania placeholderów:", error));
    }

    if (documentSelect) {
        documentSelect.addEventListener("change", updatePlaceholders);
    }

    updatePlaceholders(); // Uruchomienie na starcie
});
