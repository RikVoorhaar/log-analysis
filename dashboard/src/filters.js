import 'bootstrap'
import 'bootstrap-select'
import 'bootstrap-select/dist/css/bootstrap-select.min.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import $ from 'jquery'
import './filter.css'

class FilterRow {
  constructor(data) {
    this.row = document.createElement('div')
    this.row.classList.add('filter-row')

    // Create DOM elements for each form group
    const startDateLabel = document.createElement('label')
    startDateLabel.setAttribute('for', 'start-date')
    startDateLabel.textContent = 'Start Date:'

    const startDateInput = document.createElement('input')
    startDateInput.setAttribute('type', 'date')
    startDateInput.setAttribute('id', 'start-date')
    startDateInput.setAttribute('min', data.minDate)
    startDateInput.setAttribute('max', data.maxDate)
    startDateInput.setAttribute('value', data.minDate)

    const startDateGroup = document.createElement('div')
    startDateGroup.classList.add('form-group')
    startDateGroup.appendChild(startDateLabel)
    startDateGroup.appendChild(startDateInput)

    const endDateLabel = document.createElement('label')
    endDateLabel.setAttribute('for', 'end-date')
    endDateLabel.textContent = 'End Date:'

    const endDateInput = document.createElement('input')
    endDateInput.setAttribute('type', 'date')
    endDateInput.setAttribute('id', 'end-date')
    endDateInput.setAttribute('min', data.minDate)
    endDateInput.setAttribute('max', data.maxDate)
    endDateInput.setAttribute('value', data.maxDate)

    const endDateGroup = document.createElement('div')
    endDateGroup.classList.add('form-group')
    endDateGroup.appendChild(endDateLabel)
    endDateGroup.appendChild(endDateInput)

    const countryLabel = document.createElement('label')
    countryLabel.setAttribute('for', 'country')
    countryLabel.textContent = 'Country:'

    const countrySelect = document.createElement('select')
    countrySelect.setAttribute('id', 'country')
    countrySelect.classList.add('selectpicker')
    countrySelect.setAttribute('multiple', 'multiple')

    const countryOptions = data.countries.map(country => {
      const option = document.createElement('option')
      option.setAttribute('value', country)
      option.textContent = country
      return option
    })

    const defaultCountryOption = document.createElement('option')
    defaultCountryOption.setAttribute('value', '')
    defaultCountryOption.textContent = '<All countries>'
    countrySelect.appendChild(defaultCountryOption)
    countryOptions.forEach(option => countrySelect.appendChild(option))

    const countryGroup = document.createElement('div')
    countryGroup.classList.add('form-group')
    countryGroup.appendChild(countryLabel)
    countryGroup.appendChild(countrySelect)

    // const continentDropdown = document.createElement('div')
    // continentDropdown.setAttribute('class', 'dropdown')

    const continentLabel = document.createElement('button')
    continentLabel.setAttribute('class', 'btn btn-default dropdown-toggle')
    continentLabel.setAttribute('type', 'button')
    continentLabel.setAttribute('data-toggle', 'dropdown')
    continentLabel.setAttribute('id', 'continentDropDown')
    continentLabel.setAttribute('aria-haspopup', 'true')
    continentLabel.textContent = 'Continent'
    // continentDropdown.appendChild(continentLabel)

    const continentSelect = document.createElement('ul')
    continentSelect.setAttribute('class', 'dropdown-menu')
    continentSelect.setAttribute('aria-labelledby', 'continentDropDown')
    // continentDropdown.appendChild(continentSelect)

    const continentOptions = data.continents.map(continent => {
      // const option = document.createElement('li')
      const link = document.createElement('a')
      link.setAttribute('href', '#')
      link.classList.add('dropdown-item')
      // option.appendChild(link)
      link.textContent = continent
      return link
    })

    // const defaultContinentOption = document.createElement('li')
    // defaultContinentOption.textContent = 'All continents'
    // continentSelect.appendChild(defaultContinentOption)
    continentOptions.forEach(option => continentSelect.appendChild(option))

    const continentGroup = document.createElement('div')
    continentGroup.classList.add('dropdown')
    continentGroup.appendChild(continentLabel)
    continentGroup.appendChild(continentSelect)

    //
    // Page names
    //
    const pageNameLabel = document.createElement('label')
    pageNameLabel.setAttribute('for', 'page-name')
    pageNameLabel.textContent = 'Page Name:'

    const pageNameSelect = document.createElement('select')
    pageNameSelect.classList.add('form-select')
    pageNameSelect.setAttribute('id', 'page-name')
    pageNameSelect.setAttribute('multiple', '')


    const pageNameOptions = data.pageNames.map(pageName => {
      const option = document.createElement('option')
      option.setAttribute('value', pageName)
      option.textContent = pageName
      return option
    })

    startDateInput.addEventListener('change', this.sendData.bind(this))
    endDateInput.addEventListener('change', this.sendData.bind(this))
    countrySelect.addEventListener('change', this.sendData.bind(this))
    continentSelect.addEventListener('change', this.sendData.bind(this))
    pageNameSelect.addEventListener('change', this.sendData.bind(this))

    const defaultPageNameOption = document.createElement('option')
    defaultPageNameOption.setAttribute('value', '')
    defaultPageNameOption.textContent = '<All pages>'
    pageNameSelect.appendChild(defaultPageNameOption)
    pageNameOptions.forEach(option => pageNameSelect.appendChild(option))

    const pageNameGroup = document.createElement('div')
    pageNameGroup.classList.add('form-group')
    pageNameGroup.appendChild(pageNameLabel)
    pageNameGroup.appendChild(pageNameSelect)

    // Append form groups to the row
    this.row.appendChild(startDateGroup)
    this.row.appendChild(endDateGroup)
    this.row.appendChild(countryGroup)
    this.row.appendChild(continentGroup)
    this.row.appendChild(pageNameGroup)
    $('select').selectpicker()
  }

  sendData() {
    // Send data to Flask app
    const data = {
      startDate: this.row.querySelector('#start-date').value,
      endDate: this.row.querySelector('#end-date').value,
      country: this.row.querySelector('#country').value,
      continent: this.row.querySelector('#continent').value,
      pageName: this.row.querySelector('#page-name').value
    }

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
        console.log(data)
      })
      .catch(error => console.error(error))
  }
}

const filterRowsContainer = document.querySelector('#filter-rows')
const addFilterButton = document.querySelector('#add-filter')

const filterRows = []

let filterData
fetch('/filter-options').then(response => response.json()).then(data => {
  filterData = data
}).catch(error => console.error(error))

addFilterButton.addEventListener('click', () => {
  const filterRow = new FilterRow(filterData)
  filterRows.push(filterRow)
  filterRowsContainer.appendChild(filterRow.row)
})
$(function () {
  $('select').selectpicker();
});