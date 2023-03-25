const path = require('path')

module.exports = {
    entry: './src/filters.js',
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
            }
        ]
    }, 
    mode: 'development'
}
