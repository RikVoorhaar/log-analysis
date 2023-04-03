import "./bootstrap-loader"
// import "./filter.css"
import React, { useState, useEffect } from "react"
import { createRoot } from "react-dom/client"
import FilterContainerComponent from "./filterContainer"
import PlotlyGraph from "./plotlyGraph"

class EmptyFilterError extends Error {
    constructor(message: string) {
        super(message)
        this.name = "EmptyFilterError"
    }
}

const App = () => {
    const [plotIds, setPlotIds] = useState<string[]>([])
    const [plotsData, setPlotsData] = useState<{ [key: string]: any }>({})
    // const [filterContainerHeight, setFilterContainerHeight] = useState<number>(0)

    useEffect(() => {
        fetch("/all-plots/")
            .then((response) => response.json())
            .then((ids) => setPlotIds(ids))
            .catch((err) => console.error(err))
    }, [])

    const updatePlots = (filters: any) => {
        fetch("/filter-data/", {
            method: "POST",
            body: JSON.stringify(filters),
            headers: {
                "Content-Type": "application/json",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    return response.json().then((errorData) => {
                        if (errorData.error_code === "EMPTY_FILTERS") {
                            throw new EmptyFilterError(errorData.message)
                        } else {
                            throw new Error(errorData.message)
                        }
                    })
                }
                return response.json()
            })
            .then((rawData: Record<string, string>) => {
                const parsedData = Object.entries(rawData).reduce(
                    (
                        acc: Record<string, any>,
                        [plotId, jsonString]: [string, string]
                    ) => {
                        acc[plotId] = JSON.parse(jsonString)
                        return acc
                    },
                    {}
                )
                setPlotsData(parsedData)
            })
            .catch((err) => {
                if (err instanceof EmptyFilterError) {
                    // Do nothing;
                } else {
                    console.error(err)
                }
            })
    }

    const handleFilterDataChange = (data: any) => {
        updatePlots(data)
    }

    // const handleResize = () => {
    //     const filterContainer: HTMLDivElement | null =
    //         document.querySelector(".filter-container")
    //     if (filterContainer) {
    //         const filterContainerHeight = filterContainer.offsetHeight
    //         setFilterContainerHeight(filterContainerHeight)
    //     }
    // }

    // useEffect(() => {
    //     const plotContainer: HTMLDivElement = document.getElementById(
    //         "plot-container"
    //     ) as HTMLDivElement
    //     if (plotContainer) {
    //         plotContainer.style.paddingTop = `${filterContainerHeight}px`
    //     }
    // }, [filterContainerHeight])

    return (
        <div className="app-container" data-bs-theme="dark">
            <FilterContainerComponent
                onFilterDataChange={handleFilterDataChange}
                // onResize={handleResize}
            />
            <div id="plot-container">
                {plotIds.map((id) => (
                    <PlotlyGraph
                        key={id}
                        id={id}
                        data={plotsData[id]?.data || []}
                        layout={plotsData[id]?.layout || {}}
                        config={plotsData[id]?.config || {}}
                    />
                ))}
            </div>
        </div>
    )
}

const rootElement = document.getElementById("root")
const root = createRoot(rootElement!).render(<App />)
