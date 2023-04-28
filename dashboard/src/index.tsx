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

interface PlotlyData {
    data: any
    layout: any
    config: any
}

interface FilterDataResponse {
    plots: {
        [key: string]: string
    }
    filters: number[]
}

const App = () => {
    const [plotIds, setPlotIds] = useState<string[]>([])
    const [plotsData, setPlotsData] = useState<{ [key: string]: PlotlyData }>({})
    const [filterLengths, setFilterLengths] = useState<number[]>([])

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
                return response.json() as Promise<FilterDataResponse>
            })
            .then((response: FilterDataResponse) => {
                const parsedData = Object.entries(response.plots).reduce<
                    Record<string, PlotlyData>
                >(
                    (
                        acc: Record<string, any>,
                        [plotId, jsonString]: [string, string]
                    ) => {
                        acc[plotId] = JSON.parse(jsonString) as PlotlyData
                        return acc
                    },
                    {}
                )
                setPlotsData(parsedData)
                setFilterLengths(response.filters)
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

    return (
        <div className="app-container">
            <FilterContainerComponent
                onFilterDataChange={handleFilterDataChange}
                filterLengths={filterLengths}
            />
            <div className="container-fluid">
                <div className="row justify-content-center">
                    {plotIds.map((id) => (
                        <div
                            className="col col-12 col-md-12 col-lg-8 col-xl-6"
                            key={id}
                        >
                            <PlotlyGraph
                                key={id}
                                id={id}
                                data={plotsData[id]?.data || []}
                                layout={plotsData[id]?.layout || {}}
                                config={plotsData[id]?.config || {}}
                            />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

const rootElement = document.getElementById("root")
const root = createRoot(rootElement!).render(<App />)
