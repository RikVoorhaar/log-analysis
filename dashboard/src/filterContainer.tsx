import React, { useEffect, useRef } from "react"
import { FilterContainer } from "./filters"

interface FilterContainerComponentProps {
    onFilterDataChange: (data: any) => void
    onResize: () => void
}

const FilterContainerComponent: React.FC<FilterContainerComponentProps> = ({
    onFilterDataChange, onResize
}) => {
    const filterRowsContainerRef = useRef<HTMLDivElement>(null)
    const addFilterButtonRef = useRef<HTMLButtonElement>(null)
    const filterContainerRef = useRef<FilterContainer>()

    useEffect(() => {
        const filterRowsContainer = filterRowsContainerRef.current
        const addFilterButton = addFilterButtonRef.current

        if (!filterRowsContainer || !addFilterButton) {
            console.error("Could not find filter rows container or add filter button.")
            return
        }

        const filterContainer = new FilterContainer(
            filterRowsContainer,
            addFilterButton
        )
        filterContainerRef.current = filterContainer
        filterContainer.on("dataChange", onFilterDataChange)
        filterContainer.on("containerResize", onResize)

        // Cleanup function
        return () => {
            if (filterContainerRef.current) {
                filterContainerRef.current.off("dataChange", onFilterDataChange)
            }
        }
    }, []) // Add an empty dependency array

    return (
        <div className="filter-container">
            <h2>Filters</h2>
            <hr></hr>
            <div id="filter-rows" ref={filterRowsContainerRef}></div>
            <button
                id="add-filter"
                ref={addFilterButtonRef}
                className="btn btn-primary"
            >
                Add Filter
            </button>
        </div>
    )
}

export default FilterContainerComponent
