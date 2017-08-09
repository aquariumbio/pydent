require('../trident.js')

AQ.login_interactive().then(response => {

  AQ.User
    .find(1)
    .then(console.log)
    .catch(console.log)

}).catch(console.log)
