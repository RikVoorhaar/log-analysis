const path = require("path")
const SpeedMeasurePlugin = require("speed-measure-webpack-plugin")
const smp = new SpeedMeasurePlugin()

const webpackConfig = {
    entry: "./src/index.tsx",
    cache: {
        type: "filesystem",
    },
    output: {
        filename: "bundle.js",
        path: path.resolve(__dirname, "dist"),
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: ["style-loader", "css-loader"],
            },
            {
                test: /\.jsx?$/,
                use: ["source-map-loader"],
                enforce: "pre",
                // exclude: /node_modules/,
            },
            {
                test: /\.tsx?$/,
                use: "ts-loader",
                // exclude: /node_modules/,
            },
        ],
    },
    mode: "development",
    resolve: {
        extensions: [".tsx", ".ts", ".js"],
    },
}

module.exports = smp.wrap(webpackConfig)
// module.exports = webpackConfig
