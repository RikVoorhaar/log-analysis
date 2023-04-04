// import "bootstrap"
import "bootstrap-datepicker"
import "bootstrap-datepicker/dist/css/bootstrap-datepicker3.min.css"
import "bootstrap-select"
import "bootstrap-icons/font/bootstrap-icons.css"
import "bootstrap-select/dist/css/bootstrap-select.min.css"
import "bootstrap/dist/css/bootstrap.min.css"
import { EventEmitter } from "events"
import $ from "jquery"
import "./filter.css"

const MAX_NUM_FILTERS: number = 6

abstract class FilterElement {
    public container: HTMLDivElement
    protected eventEmitter: EventEmitter

    constructor() {
        this.container = document.createElement("div")
        this.eventEmitter = new EventEmitter()
    }

    abstract render(): void

    abstract getValues(): string[]

    public on(event: string, listener: (...args: any[]) => void) {
        this.eventEmitter.on(event, listener)
    }
}

class MultiSelect extends FilterElement {
    private values: string[]
    private label: string

    constructor(values: string[], label: string) {
        super()
        this.values = values
        this.label = label

        this.container.classList.add("form-group", "multi-select-group")
        this.container.innerHTML = `
      <select multiple id=${this.label}>
        ${this.values.map((value) => `<option>${value}</option>`).join("")}
      </select>
    `

        this.container.addEventListener("change", () => {
            this.eventEmitter.emit("change", undefined)
        })
    }

    public render(): void {
        $(this.container).find("select").selectpicker({
            liveSearch: true,
            actionsBox: true,
            header: this.label,
            liveSearchNormalize: true,
            noneSelectedText: `Select ${this.label}`,
            width: "100%",
        })
    }

    getValues(): string[] {
        const selectEl = this.container.querySelector("select") as HTMLSelectElement
        return Array.from(selectEl.selectedOptions).map((option) => option.value)
    }
}

class DatePicker extends FilterElement {
    private min_date: string
    private max_date: string

    constructor(min_date: string, max_date: string) {
        super()
        this.min_date = min_date
        this.max_date = max_date

        this.container.classList.add("input-daterange")
        this.container.classList.add("input-group")
        this.container.setAttribute("id", "datepicker")

        this.container.innerHTML = `
        <div class="input-daterange input-group input-group-sm" id="datepicker">
            <input type="text" class="form-control" name="start" />
                <div class="input-group-append input-group-prepend">
                    <span class="input-group-text">to</span>
                </div>
            <input type="text" class="form-control" name="end" />
        </div>
        `

        const inputs = Array.from(this.container.querySelectorAll("input"))

        inputs.forEach((input) => {
            input.addEventListener("input", () => {
                this.eventEmitter.emit("change", undefined)
            })
        })
    }

    public render(): void {
        $(this.container).datepicker({
            format: "yyyy-mm-dd",
            startDate: this.min_date,
            endDate: this.max_date,
            startView: 1,
            maxViewMode: 3,
            immediateUpdates: true,
            autoclose: true,
            clearBtn: true,
            keepEmptyValues: true,
            weekStart: 1
        })
        $(this.container).datepicker("update", [this.min_date, this.max_date])
        $(this.container).datepicker().on("changeDate", () => {
            this.eventEmitter.emit("change", undefined)
        }) 
    }

    getValues(): string[] {
        const inputs = Array.from(this.container.querySelectorAll("input"))
        return inputs.map((input) => input.value)
    }
}

class FilterRow {
    public row: HTMLDivElement
    private filters: Record<string, FilterElement>
    private eventEmitter: EventEmitter
    public deleteButton: HTMLButtonElement
    public index: number

    constructor(data: FilterOptionsInterface, index: number) {
        this.index = index
        this.row = document.createElement("div")
        this.row.classList.add("filter-row")

        this.filters = {
            dateRange: new DatePicker(data.minDate, data.maxDate),
            countries: new MultiSelect(data.countries, "Country"),
            continents: new MultiSelect(data.continents, "Continent"),
            pageNames: new MultiSelect(data.pageNames, "Page Name"),
        }

        this.deleteButton = document.createElement("button")
        this.deleteButton.classList.add("btn", "btn-delete", "btn-sm")
        this.deleteButton.innerHTML = '<i class="bi bi-x-lg"></i>'
        this.deleteButton.setAttribute("aria-label", "Delete")
        this.deleteButton.addEventListener("click", () => {
            this.delete()
        })
        this.row.appendChild(this.deleteButton)

        this.eventEmitter = new EventEmitter()

        for (const key in this.filters) {
            const filter = this.filters[key]
            // filter.container.addEventListener('change', this.sendData.bind(this))
            filter.on("change", () => {
                this.eventEmitter.emit("change", undefined)
            })
            this.row.appendChild(filter.container)
        }
    }

    public getData(): { [key: string]: string[] } {
        const data: { [key: string]: string[] } = {}
        for (const key in this.filters) {
            const filter = this.filters[key]
            data[key] = filter.getValues()
        }
        data["index"] = [this.index.toString()]
        return data
    }

    public on(event: string, listener: (...args: any[]) => void) {
        this.eventEmitter.on(event, listener)
    }

    public render(): void {
        for (const key in this.filters) {
            const filter = this.filters[key]
            filter.render()
        }
    }

    private delete(): void {
        this.row.remove()
        // Emit an event to let the FilterContainer know that this FilterRow was deleted
        this.eventEmitter.emit("delete", this)
    }
}

interface FilterOptionsInterface {
    minDate: string
    maxDate: string
    countries: string[]
    continents: string[]
    pageNames: string[]
}

export class FilterContainer extends EventEmitter {
    private filterOptions!: FilterOptionsInterface
    private filterRowList!: FilterRow[]
    private filterRowsContainer!: HTMLDivElement
    private addFilterButton!: HTMLButtonElement

    constructor(
        filterRowsContainer: HTMLDivElement,
        addFilterButton: HTMLButtonElement
    ) {
        super()
        // const filterRowsContainer = document.querySelector<HTMLDivElement>('#filter-rows')
        // const addFilterButton = document.querySelector<HTMLButtonElement>('#add-filter')
        if (!filterRowsContainer || !addFilterButton) {
            console.error("Could not find filter rows container or add filter button.")
            return
        }

        this.filterRowsContainer = filterRowsContainer
        this.addFilterButton = addFilterButton

        this.filterRowList = []

        addFilterButton.disabled = true
        addFilterButton.addEventListener("click", () => {
            this.addFilter()
        })

        fetch("/filter-options")
            .then((response) => response.json())
            .then((data) => {
                this.filterOptions = data
                this.addFilter()
                addFilterButton.disabled = false
            })
            .catch((error) => console.error(error))
    }

    private addFilter(): void {
        const filterRow = new FilterRow(this.filterOptions, this.filterRowList.length)
        this.filterRowList.push(filterRow)
        this.filterRowsContainer.appendChild(filterRow.row)
        filterRow.render()
        filterRow.on("change", () => {
            this.emitDataChangeEvent()
        })
        filterRow.on("delete", (deletedFilterRow: FilterRow) => {
            const index = this.filterRowList.indexOf(deletedFilterRow)
            if (index !== -1) {
                this.filterRowList.splice(index, 1)
            }
            this.emitDataChangeEvent()
            this.emitResizeEvent()
        })
        this.emitDataChangeEvent()
        this.emitResizeEvent()
    }

    private updateIndices(): void {
        this.filterRowList.forEach((filterRow, index) => {
            filterRow.index = index
        })
    }

    public getData(): { [key: string]: string[] }[] {
        const data: { [key: string]: string[] }[] = []
        for (const filterRow of this.filterRowList) {
            const row_data = filterRow.getData()
            data.push(row_data)
        }
        return data
    }

    public emitDataChangeEvent() {
        this.emit("dataChange", this.getData())
    }

    public emitResizeEvent() {
        if (this.filterRowList.length >= MAX_NUM_FILTERS) {
            this.addFilterButton.disabled = true
        } else {
            this.addFilterButton.disabled = false
        }

        if (this.filterRowList.length == 1) {
            this.filterRowList[0].deleteButton.disabled = true
        } else {
            this.filterRowList.forEach((filterRow) => {
                filterRow.deleteButton.disabled = false
            })
        }
        this.updateIndices()
        this.emit("containerResize")
    }
}
