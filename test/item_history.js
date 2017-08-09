require('../trident.js')

AQ.login_interactive().then(response => {

  AQ.Item.find(99539).then(item => {
    console.log(item);
    item.get_history().then(console.log)
  });

}).catch(console.log)
