require('../trident.js')

AQ.login_interactive()
  .then(response => {

    AQ.SampleType
      .all()
      .then(console.log)
      .catch(console.log)

  }).catch(console.log)
