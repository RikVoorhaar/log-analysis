import React, { useState, useEffect } from "react"
import ReactDOM from "react-dom"
import { createRoot } from "react-dom/client"
import FilterContainerComponent from "./filterContainer"
import PlotlyGraph from "./plotlyGraph"

const App = () => {
    const [plotIds, setPlotIds] = useState<string[]>([])
    const [plotsData, setPlotsData] = useState<{ [key: string]: any }>({})

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
            .then((response) => response.json())
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

            .catch((err) => console.error(err))
    }

    const handleFilterDataChange = (data: any) => {
        updatePlots(data)
    }

    return (
        <div>
            <h1> My dashboard</h1>
            <FilterContainerComponent onFilterDataChange={handleFilterDataChange} />
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
    )
}

const rootElement = document.getElementById("root")
const root = createRoot(rootElement!).render(<App />)
