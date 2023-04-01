import React, { useState, useEffect } from "react"
import ReactDOM from "react-dom"
import { createRoot } from "react-dom/client"
import FilterContainerComponent from "./filterContainer"
import PlotlyGraph from "./plotlyGraph"

const App = () => {
    const [plotIds, setPlotIds] = useState<string[]>([])
    const [plotsData, setPlotsData] = useState<any[]>([])

    useEffect(() => {
        fetch("/all-plots/")
            .then((response) => response.json())
            .then((ids) => setPlotIds(ids))
            .catch((err) => console.error(err))
    }, [])

    const updatePlots = (data: any) => {
        fetch("/filter-data/", {
            method: "POST",
            body: JSON.stringify(data),
            headers: {
                "Content-Type": "application/json",
            },
        })
            .then((response) => response.json())
            .then((data) => setPlotsData(data))
            .catch((err) => console.error(err))
    }

    const handleFilterDataChange = (data: any) => {
        updatePlots(data)
    }

    return (
        <div>
            <h1> My dashboard</h1>
            <FilterContainerComponent onFilterDataChange={handleFilterDataChange} />
            {plotIds.map((id, index) => (
                <PlotlyGraph
                    key={id}
                    id={id}
                    data={plotsData[index]?.data || []}
                    layout={plotsData[index]?.layout || {}}
                    config={plotsData[index]?.config || {}}
                />
            ))}
        </div>
    )
}

const rootElement = document.getElementById("root")
const root = createRoot(rootElement!).render(<App />)
