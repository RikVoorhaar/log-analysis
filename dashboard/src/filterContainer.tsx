import React, { useEffect, useRef, useState } from "react"
import { FilterContainer } from "./filters"

interface FilterContainerComponentProps {
    onFilterDataChange: (data: any) => void
    // onResize: () => void
}

const FilterContainerComponent: React.FC<FilterContainerComponentProps> = ({
    onFilterDataChange,
    // onResize,
}) => {
    const filterRowsContainerRef = useRef<HTMLDivElement>(null)
    const addFilterButtonRef = useRef<HTMLButtonElement>(null)
    const filterContainerRef = useRef<FilterContainer>()
    const mainDivRef = useRef<HTMLDivElement>(null)
    const firstLoadRef = useRef<boolean>(true)
    const [showFilterContainer, setShowFilterContainer] = useState<boolean>(true)

    const toggleFilterContainer = () => {
        setShowFilterContainer(!showFilterContainer)
    }
    const filterContainerStyle = {
        maxHeight: showFilterContainer ? "100vh" : "0",
        transition: "max-height 0.5s ease-in-out",
    }

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
        // filterContainer.on("containerResize", onResize)

        // Cleanup function
        return () => {
            if (filterContainerRef.current) {
                filterContainerRef.current.off("dataChange", onFilterDataChange)
            }
        }
    }, []) // Add an empty dependency array

    const handleTransitionEnd = (e: React.TransitionEvent<HTMLDivElement>) => {
        if (e.propertyName === "max-height") {
            if (showFilterContainer && mainDivRef.current) {
                mainDivRef.current.style.overflowY = "visible"
            }
        }
    }

    useEffect(() => {
        if (mainDivRef.current) {
            if (firstLoadRef.current) {
                mainDivRef.current.style.overflowY = "visible"
                firstLoadRef.current = false
            } else {
                mainDivRef.current.style.overflowY = "hidden"
            }
        }
    }, [showFilterContainer])

    return (
        <div className="filter-container" ref={mainDivRef}>
            <button onClick={toggleFilterContainer} className="btn btn-outline-primary">
                {showFilterContainer ? "Hide" : "Show"} filters
            </button>
            <div style={filterContainerStyle} onTransitionEnd={handleTransitionEnd}>
                <hr></hr>
                <button
                    id="add-filter"
                    ref={addFilterButtonRef}
                    className="btn btn-outline-primary"
                    style={{ padding: "0px 4px", marginBottom: "10px" }}
                >
                    <i className="bi bi-plus-lg"></i> Add Filter
                </button>
                <div id="filter-rows" ref={filterRowsContainerRef}></div>
            </div>
        </div>
    )
}

export default FilterContainerComponent
