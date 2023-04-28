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
        <div class="d-flex align-items-center w-100">
          <select multiple id=${this.label}>
            ${this.values.map((value) => `<option>${value}</option>`).join("")}
          </select>
        </div>
      `

        this.container.addEventListener("change", () => {
            this.eventEmitter.emit("change", undefined)
        })
    }

    public render(): void {
        $(this.container)
            .find("select")
            .selectpicker({
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
        <div class="input-daterange input-group input-group-extra-sm" id="datepicker">
            <input type="text" class="form-control smaller-input-text" name="start" />
                <div class="input-group-append input-group-prepend">
                    <span class="input-group-text">to</span>
                </div>
            <input type="text" class="form-control smaller-input-text" name="end" />
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
            weekStart: 1,
        })
        $(this.container).datepicker("update", [this.min_date, this.max_date])
        $(this.container)
            .datepicker()
            .on("changeDate", () => {
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
    private color!: string
    private colorSquare!: HTMLElement
    private countAlert!: HTMLDivElement

    constructor(data: FilterOptionsInterface, index: number, colors: string[]) {
        this.index = index
        this.row = document.createElement("div")
        this.row.classList.add("filter-row", "d-flex", "align-items-center", "mb-3")

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
        this.colorSquare = this.createSquare()
        this.updateColor(colors)
        this.row.appendChild(this.colorSquare)

        this.eventEmitter = new EventEmitter()

        for (const key in this.filters) {
            const filter = this.filters[key]
            filter.on("change", () => {
                this.eventEmitter.emit("change", undefined)
            })
            this.row.appendChild(filter.container)
        }

        this.countAlert = this.createCountAlert()
        this.updateCount(0)
        this.row.appendChild(this.countAlert)
    }

    public updateColor(colors: string[]) {
        this.color = colors[this.index]
        this.colorSquare.style.backgroundColor = this.color
        this.colorSquare.textContent = (this.index + 1).toString()
    }

    private createSquare(): HTMLElement {
        const square = document.createElement("span")
        square.textContent = " "
        square.classList.add("badge", "badge-pill", "badge-primary")
        square.style.width = "20px"
        square.style.height = "20px"
        return square
    }

    private createCountAlert(): HTMLDivElement {
        const counter = document.createElement("div")
        counter.role = "alert"
        counter.classList.add("alert", "alert-primary")
        return counter
    }

    public updateCount(count: number): void {
        if (this.countAlert) {
            this.countAlert.textContent = count.toString() + " hits"
        }
        this.countAlert.classList.remove("alert-primary", "alert-danger")

        if (count === 0) {
            this.countAlert.classList.add("alert-danger")
        } else {
            this.countAlert.classList.add("alert-primary")
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
    filterOptions!: FilterOptionsInterface
    filterRowList!: FilterRow[]
    filterRowsContainer!: HTMLDivElement
    addFilterButton!: HTMLButtonElement
    colors: string[] = []

    constructor(
        filterRowsContainer: HTMLDivElement,
        addFilterButton: HTMLButtonElement
    ) {
        super()
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

        fetch("/colors")
            .then((response) => response.json())
            .then((data) => {
                this.colors = data
                this.updateIndices()
            })
            .catch((error) => console.error(error))
    }

    private addFilter(): void {
        const filterRow = new FilterRow(
            this.filterOptions,
            this.filterRowList.length,
            this.colors
        )
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
            this.emitResizeEvent()
            this.emitDataChangeEvent()
        })
        this.emitResizeEvent()
        this.emitDataChangeEvent()
    }

    private updateIndices(): void {
        this.filterRowList.forEach((filterRow, index) => {
            filterRow.index = index
            filterRow.updateColor(this.colors)
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

    public updateFilterLengths(filterLengths: number[]): void {
        filterLengths.forEach((length, index) => {
            this.filterRowList[index].updateCount(length)
        })
    }
}
