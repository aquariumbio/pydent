require('../trident.js')

AQ.login_interactive().then(response => {

  AQ.Plan.find(513).then(plan => {
    plan.get_data_associations().then(console.log);
  }).catch(console.log)

})
