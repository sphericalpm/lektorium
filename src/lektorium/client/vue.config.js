const path = require('path');
const webpack = require('webpack');

module.exports = {
  outputDir: path.resolve(__dirname, 'build'),
  configureWebpack: {
    plugins: [
      new webpack.ProvidePlugin({
        $: 'jquery',
        jquery: 'jquery',
        'window.jQuery': 'jquery',
        jQuery: 'jquery'
      })
    ]
  }
};
