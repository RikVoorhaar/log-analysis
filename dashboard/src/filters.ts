import 'bootstrap'
import 'bootstrap-select'
import 'bootstrap-select/dist/css/bootstrap-select.min.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import $ from 'jquery'
import './filter.css'

init()

class MultiSelect {
  private values: string[];
  private label: string;

  constructor(values: string[], label: string) {
    this.values = values;
    this.label = label;

    this.render();
  }

  private render() {
    const container = document.createElement('div');
    container.classList.add('form-group')
    container.innerHTML = `
      <label>${this.label}</label>
      <select multiple id=${this.label}>
        ${this.values.map(value => `<option>${value}</option>`).join('')}
      </select>
    `;
    document.body.appendChild(container);
  }

  getSelectedValues(): string[] {
    const selectEl = document.querySelector('select') as HTMLSelectElement;
    return Array.from(selectEl.selectedOptions).map(option => option.value);
  }
}


class FilterRow {
  public row: HTMLDivElement

  constructor(data: FilterOptionsInterface) {
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
  }

  sendData() {
    // Send data to Flask app
    const startDateInput = this.row.querySelector<HTMLInputElement>('#start-date');
    const endDateInput = this.row.querySelector<HTMLInputElement>('#end-date');
    const countrySelect = this.row.querySelector<HTMLSelectElement>('#country');
    const continentSelect = this.row.querySelector<HTMLSelectElement>('#continent');
    const pageNameSelect = this.row.querySelector<HTMLSelectElement>('#page-name');

    if (!startDateInput || !endDateInput || !countrySelect || !continentSelect || !pageNameSelect) {
      console.error('One or more inputs could not be found.');
      return;
    }

    const data = {
      startDate: startDateInput.value,
      endDate: endDateInput.value,
      country: countrySelect.value,
      continent: continentSelect.value,
      pageName: pageNameSelect.value
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

interface FilterOptionsInterface {
  minDate: string;
  maxDate: string;
  countries: string[];
  continents: string[];
  pageNames: string[];
}

function init(): void {
  let filterOptions: FilterOptionsInterface
  fetch('/filter-options').then(response => response.json()).then(data => {
    filterOptions = data
  }).catch(error => console.error(error))

  const filterRowsContainer = document.querySelector<HTMLDivElement>('#filter-rows')
  const addFilterButton = document.querySelector<HTMLButtonElement>('#add-filter')
  if (!filterRowsContainer || !addFilterButton) {
    console.error('Could not find filter rows container or add filter button.')
    return
  }

  const filterRows = []

  addFilterButton.addEventListener('click', () => {
    const filterRow = new FilterRow(filterOptions)
    filterRows.push(filterRow)
    filterRowsContainer.appendChild(filterRow.row)
    $('select').selectpicker()
  })
  $(function () {
    $('select').selectpicker();
  });
}
