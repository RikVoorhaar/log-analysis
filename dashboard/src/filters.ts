import 'bootstrap'
import 'bootstrap-datepicker'
import 'bootstrap-datepicker/dist/css/bootstrap-datepicker3.min.css'
import 'bootstrap-select'
import 'bootstrap-select/dist/css/bootstrap-select.min.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import { EventEmitter } from 'events'
import $ from 'jquery'
import './filter.css'


abstract class FilterElement {
  public container: HTMLDivElement;
  protected eventEmitter: EventEmitter;

  constructor() {
    this.container = document.createElement('div');
    this.eventEmitter = new EventEmitter();
  }

  abstract render(): void;

  abstract getValues(): string[];

  public on(event: string, listener: (...args: any[]) => void) {
    this.eventEmitter.on(event, listener);
  }
}


class MultiSelect extends FilterElement {
  private values: string[];
  private label: string;

  constructor(values: string[], label: string) {
    super()
    this.values = values;
    this.label = label;

    this.container.classList.add('form-group')
    this.container.innerHTML = `
      <select multiple id=${this.label} data-live-search="true">
        ${this.values.map(value => `<option>${value}</option>`).join('')}
      </select>
    `;

    this.container.addEventListener('change', () => {
      this.eventEmitter.emit('change', undefined)
    })
  }

  public render(): void {
    $(this.container).find('select').selectpicker()
  }

  getValues(): string[] {
    const selectEl = this.container.querySelector('select') as HTMLSelectElement;
    return Array.from(selectEl.selectedOptions).map(option => option.value);
  }
}

class DatePicker extends FilterElement {
  private min_date: string;
  private max_date: string;

  constructor(min_date: string, max_date: string) {
    super()
    this.min_date = min_date;
    this.max_date = max_date;

    this.container.classList.add('input-daterange')
    this.container.classList.add('input-group')
    this.container.setAttribute('id', 'datepicker')

    this.container.innerHTML = `
      <div class="input-daterange input-group" id="datepicker">
        <input type="text" class="input-sm form-control" name="start" />
        <span class="input-group-addon">to</span>
        <input type="text" class="input-sm form-control" name="end" />
      </div>
    `

    const inputs = Array.from(this.container.querySelectorAll('input'));

    inputs.forEach(input => {
      input.addEventListener('change', () => {
        this.eventEmitter.emit('change', undefined);
      });
    });
  }

  public render(): void {
    $(this.container).datepicker({
      format: 'yyyy-mm-dd',
      startDate: this.min_date,
      endDate: this.max_date,
      startView: 1,
      maxViewMode: 3,
      immediateUpdates: true,
      autoclose: true,
      clearBtn: true,
    })
    $(this.container).datepicker('update', [this.min_date, this.max_date])
  }

  getValues(): string[] {
    const inputs = Array.from(this.container.querySelectorAll('input'));
    return inputs.map(input => input.value);
  }

}


class FilterRow {
  public row: HTMLDivElement
  private filters: Record<string, FilterElement>;
  private eventEmitter: EventEmitter;
  private deleteButton: HTMLButtonElement;

  constructor(data: FilterOptionsInterface) {
    this.row = document.createElement('div')
    this.row.classList.add('filter-row')

    this.filters = {
      'dateRange': new DatePicker(data.minDate, data.maxDate),
      'countries': new MultiSelect(data.countries, 'Country'),
      'continents': new MultiSelect(data.continents, 'Continent'),
      'pageNames': new MultiSelect(data.pageNames, 'Page Name')
    }

    this.deleteButton = document.createElement('button');
    this.deleteButton.classList.add('btn', 'btn-primary')
    this.deleteButton.textContent = 'Delete';
    this.deleteButton.addEventListener('click', () => {
      this.delete();
    });
    this.row.appendChild(this.deleteButton);


    this.eventEmitter = new EventEmitter();

    for (const key in this.filters) {
      const filter = this.filters[key];
      // filter.container.addEventListener('change', this.sendData.bind(this))
      filter.on(
        'change', () => {
          this.eventEmitter.emit('change', undefined)
        }
      )
      this.row.appendChild(filter.container)
    }
  }

  public getData(): { [key: string]: string[] } {
    const data: { [key: string]: string[] } = {};
    for (const key in this.filters) {
      const filter = this.filters[key];
      data[key] = filter.getValues();
    }
    return data
  }

  public on(event: string, listener: (...args: any[]) => void) {
    this.eventEmitter.on(event, listener);
  }


  public render(): void {
    for (const key in this.filters) {
      const filter = this.filters[key];
      filter.render()
    }
  }

  private delete(): void {
    this.row.remove();
    // Emit an event to let the FilterContainer know that this FilterRow was deleted
    this.eventEmitter.emit('delete', this);
  }

}

interface FilterOptionsInterface {
  minDate: string;
  maxDate: string;
  countries: string[];
  continents: string[];
  pageNames: string[];
}

class FilterContainer {
  private filterOptions!: FilterOptionsInterface;
  private filterRowList!: FilterRow[];
  private filterRowsContainer!: HTMLDivElement;

  constructor() {
    const filterRowsContainer = document.querySelector<HTMLDivElement>('#filter-rows')
    const addFilterButton = document.querySelector<HTMLButtonElement>('#add-filter')
    if (!filterRowsContainer || !addFilterButton) {
      console.error('Could not find filter rows container or add filter button.')
      return
    }

    this.filterRowsContainer = filterRowsContainer

    this.filterRowList = []

    addFilterButton.disabled = true
    addFilterButton.addEventListener('click', () => {
      this.addFilter()
    })

    fetch('/filter-options').then(response => response.json()).then(data => {
      this.filterOptions = data
      this.addFilter()
      addFilterButton.disabled = false
    }).catch(error => console.error(error))
  }

  private addFilter(): void {
    const filterRow = new FilterRow(this.filterOptions)
    this.filterRowList.push(filterRow)
    this.filterRowsContainer.appendChild(filterRow.row)
    filterRow.render()
    filterRow.on('change', () => {
      this.sendData()
    })
    filterRow.on('delete', (deletedFilterRow: FilterRow) => {
      const index = this.filterRowList.indexOf(deletedFilterRow);
      if (index !== -1) {
        this.filterRowList.splice(index, 1);
      }
      this.sendData()
    });
    this.sendData()
  }

  public getData(): { [key: string]: string[] }[] {
    const data: { [key: string]: string[] }[] = [];
    for (const filterRow of this.filterRowList) {
      const row_data = filterRow.getData()
      data.push(row_data)
    }
    return data
  }

  public sendData() {
    fetch('/filter-data', {
      method: 'POST',
      body: JSON.stringify(this.getData()),
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

function init(): void {
  const filterContainer = new FilterContainer()
}

init()