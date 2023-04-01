import React, { useRef } from "react"
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

    return <Plot ref={plotRef} data={data} layout={layout} config={config} />
}
export default PlotlyGraph
