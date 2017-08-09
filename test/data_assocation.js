require('../trident.js')

AQ.login_interactive()
  .then(response => {

    AQ.Plan.find(513).then(plan => {
      console.log(plan)
      console.log("-------------------------")
      plan.get_data_associations().then(das =>
        console.log(das)
      );
    })

  })
