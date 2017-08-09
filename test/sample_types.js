require("../trident.js");

// AQ.get("/signin").then(result => {
//
//   var re = /value="[0-9a-zA-Z=]*"/;
//   authkey = result.match(re)[0].split('"')[1];
//   console.log(authkey);
//   AQ.authkey = "a" + authkey;

  AQ.login_interactive()
    .then(response => {

      // AQ.get("/browser/all")
      //   .then(x => 1)
      //   .catch(console.log)

      // AQ.User
      //   .find(1)
      //   .then(console.log)
      //   .catch(console.log)

      AQ.SampleType
        .all()
        .then(sts => {
          aq.each(sts, st => console.log("" + st.id + ": " + st.name))
        })
        .catch(console.log);

    }).catch(console.log);
