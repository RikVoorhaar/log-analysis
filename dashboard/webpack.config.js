const path = require("path")
const TerserPlugin = require("terser-webpack-plugin")

module.exports = (env, { mode }) => {
    const isProduction = mode === "production"

    return {
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
                },
                {
                    test: /\.tsx?$/,
                    use: "ts-loader",
                },
            ],
        },
        mode,
        resolve: {
            extensions: [".tsx", ".ts", ".js"],
        },
        optimization: isProduction
            ? {
                  minimize: true,
                  minimizer: [
                      new TerserPlugin({
                          parallel: true,
                      }),
                  ],
              }
            : {},
    }
}
