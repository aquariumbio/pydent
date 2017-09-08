global.AQ = {};

require('./config/trident.js');

require('./core/AQ.js');
require('./core/login.js');
require('./core/base.js');
require('./core/record.js');

require('./models/item.js');

AQ.init();

module.exports = {};
