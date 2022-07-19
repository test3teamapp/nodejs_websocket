const bcrypt = require("bcryptjs");
const mongoose = require("mongoose");

const UserModel = require("../models/user.js");

const saltRounds = 10;

function createANewUser(username, password, callback) {
  const newUserDbDocument = new UserModel({
    username: username,
    password: password,
  });

  newUserDbDocument.save(function (error) {
    if (error) {
      callback(error);
    } else {
      callback();
    }
  });
}

main().catch((err) => console.log(err));

async function main() {
  const uname = "cang";
  const pass = "Olatalefta2U";

  console.log("Creating user " + uname );
  await mongoose.connect("mongodb://localhost:27017/webchatroom");

  // if user exists ...

  UserModel.exists({ username: uname }).exec((err, user) => {
    if (err){
        console.log("Error while searching for existing user: " + err );
    }else {
	if (user){ // if not found is null
          console.log("Abort: I found existing user by that name: ");
	}else {
	  console.log("Did not find user by that name. Creating...");
	  createANewUser(uname, pass, function (error) {
    	    if (error) {
              console.log("failed : " + error);
            } else {
              console.log("done");
    	    }
  	  });
	}
    }
  });
}

//if (require.main === module) {
//  main();
//}
