const path = require('path')

module.exports = {
    entry: './src/filters.ts',
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, 'assets')
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            },
            {
                test: /\.js$/,
                use: ['source-map-loader'],
                enforce: 'pre'
            },
            {
                test: /\.tsx?$/,
                use: 'ts-loader',
                exclude: /node_modules/
            }

        ]
    }, 
    mode: 'development',
    resolve : {
        extensions: ['.tsx', '.ts', '.js']
    }

}
