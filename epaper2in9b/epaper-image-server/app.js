const express = require("express");
const exphbs  = require('express-handlebars');
const sharp = require('sharp');
const pino = require('express-pino-logger')()

var app = express();

app.use(pino);
app.use(express.urlencoded());
app.use(express.json());
app.engine('handlebars', exphbs());
app.set('view engine', 'handlebars');

function handle_image_request(req, res, primary) {
    let imageName = req.query.image;
    if(typeof imageName === "undefined") {
        imageName = "test.png";
    }
    let imagePath = "sample-images/" + imageName;

    sharp(imagePath).rotate(90).raw().toBuffer({ resolveWithObject: true })
        .then(image => {
            // Binary magic with JavaScript, please close your eyes!
            console.log(image);
            const width = image.info.width;
            const height = image.info.height;
            console.log("Image size: " + width + " " + height);
            const bytes = width * height * 3;
            const output = Buffer.alloc((width * height) / 8);
            let rotatingBits = 0;
            let bytesWritten = 0;

            for(i = 0; i < bytes;) {
                let pixelCount = i / 3 + 1;
                let red = image.data.readUInt8(i++);
                let green = image.data.readUInt8(i++);
                let blue = image.data.readUInt8(i++);

                if(primary) {
                    // Map black as 0, nother colors as 1
                    if(red == 0 && green == 0 && blue == 0) {
                        rotatingBits |= 0;
                    } else {
                        rotatingBits |= 1;
                    }
                } else {
                    // Map red or yellow as 0, other color as 1
                    if(red == 255 && (green == 0 || green == 255) && blue == 0) {
                        rotatingBits |= 0;
                    } else {
                        rotatingBits |= 1;
                    }
                }
                
                if(pixelCount % 8 == 7) {
                    output.writeUInt8(rotatingBits, bytesWritten);
                    bytesWritten++;
                    rotatingBits = 0;
                } else {
                    rotatingBits = rotatingBits << 1;
                }
            }

            res.contentType("application/octet-stream");
            res.write(output, "binary");
            res.end(undefined, "binary");
        })
        .catch(err => {
            console.error(err);
            //req.log.err("Fail!", err);
            res.status(500);
        });

}

// For browser
app.get('/', function (req, res) {
    let renderDataObj = {};    
    res.render('home', renderDataObj);
});

// Request for primary bytearray
app.get('/primary', function (req, res) {
    handle_image_request(req, res, true);
});

// Request for secondary bytearray
app.get('/secondary', function (req, res) {
    handle_image_request(req, res, false);
});

app.use(express.static("public"));

app.listen(8080, () => {
    pino.logger.info("Server running on port " + 8080);
});