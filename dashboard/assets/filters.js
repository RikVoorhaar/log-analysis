document.addEventListener('DOMContentLoaded', function () {

    const button = document.querySelector('#my-button');
    button.addEventListener('click', () => {
        fetch('/my-flask-route')
            .then(response => response.json())
            .then(data => {
                // handle the data returned by the Flask server
            });
    });
});

class FilterRow {
    constructor() {
        this.row = document.createElement('div');
        this.row.classList.add('filter-row');

        // Generate HTML for the row
        this.row.innerHTML = `
        <div class="form-group">
          <label for="start-date">Start Date:</label>
          <input type="date" id="start-date">
        </div>
        <div class="form-group">
          <label for="end-date">End Date:</label>
          <input type="date" id="end-date">
        </div>
        <div class="form-group">
          <label for="country">Country:</label>
          <select id="country">
            <option value="">-- Select a country --</option>
            <option value="usa">USA</option>
            <option value="canada">Canada</option>
            <option value="mexico">Mexico</option>
          </select>
        </div>
        <div class="form-group">
          <label for="continent">Continent:</label>
          <select id="continent">
            <option value="">-- Select a continent --</option>
            <option value="north-america">North America</option>
            <option value="south-america">South America</option>
            <option value="europe">Europe</option>
            <option value="asia">Asia</option>
            <option value="africa">Africa</option>
            <option value="australia">Australia</option>
          </select>
        </div>
        <div class="form-group">
          <label for="page-name">Page Name:</label>
          <select id="page-name">
            <option value="">-- Select a page name --</option>
            <option value="home">Home</option>
            <option value="about">About</option>
            <option value="contact">Contact</option>
            <option value="blog">Blog</option>
          </select>
        </div>
      `;

        // Initialize event listeners for form elements
        const startDateInput = this.row.querySelector('#start-date');
        const endDateInput = this.row.querySelector('#end-date');
        const countrySelect = this.row.querySelector('#country');
        const continentSelect = this.row.querySelector('#continent');
        const pageNameSelect = this.row.querySelector('#page-name');

        startDateInput.addEventListener('change', this.sendData.bind(this));
        endDateInput.addEventListener('change', this.sendData.bind(this));
        countrySelect.addEventListener('change', this.sendData.bind(this));
        continentSelect.addEventListener('change', this.sendData.bind(this));
        pageNameSelect.addEventListener('change', this.sendData.bind(this));
    }

    sendData() {
        // Send data to Flask app
        const data = {
            startDate: this.row.querySelector('#start-date').value,
            endDate: this.row.querySelector('#end-date').value,
            country: this.row.querySelector('#country').value,
            continent: this.row.querySelector('#continent').value,
            pageName: this.row.querySelector('#page-name').value,
        };

        fetch('/my-flask-route', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                // Handle response
                console.log(data);
            })
            .catch(error => console.error(error));
    }
}

const filterRowsContainer = document.querySelector('#filter-rows');
const addFilterButton = document.querySelector('#add-filter');

const filterRows = [];

addFilterButton.addEventListener('click', () => {
    const filterRow = new FilterRow();
    filterRows.push(filterRow);
    filterRowsContainer.appendChild(filterRow.row);
});