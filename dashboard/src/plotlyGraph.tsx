import React, { useEffect, useRef } from "react"
import Plot from "react-plotly.js"

interface PlotlyGraphProps {
    id: string
    data: any
    layout: any
    config: any
}

const PlotlyGraph: React.FC<PlotlyGraphProps> = ({ id, data, layout, config }) => {
    const plotRef = useRef<Plot>(null)

    const updatePlot = (newData: any) => {
        if (plotRef.current) {
            plotRef.current.setState({ data: newData })
        }
    }

    useEffect(() => {
        updatePlot(data)
    }, [data])

    return <Plot ref={plotRef} data={data} layout={layout} config={config}/>
}
export default PlotlyGraph
