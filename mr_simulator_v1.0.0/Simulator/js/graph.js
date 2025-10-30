import { Mx, MxMean,  Mxy, MxyMean, Bxy, single_Mode, gradient_Mode,  buttonEvents, sequence_reader } from "./Bloch_Simulator.js"

var degree_var = 0
export function Events(eventType, degree, button_type, file){

    switch(eventType){
        case "button":
            buttonEvents(degree, button_type);
            break;
        
        case "file_reader":
            console.log("Into simulator file");
            sequence_reader(file);
            break;
    }
    
    

}



    
var dpsMx = [];
var dpsMxy = [];        //datapoints
var dpsBxy = [];



var atomValue = new CanvasJS.Chart("Mx/Mxy", {
    backgroundColor: "transparent",
	title:{
		text: ""                                                //title of the graph              
	},

    axisX:{
        title: "time [ms], Δt = 100ms",
        labelFontSize: 0,                                               //setting it to zero, so it disappears (dont need that here)
        titleFontColor: "rgb(255, 255, 255)",
        valueFormatString: "s.L' s'"
      },

      axisY:{
        title: "Amplitude [T]",
        labelFontSize: 0,
        titleFontColor: "rgb(255, 255, 255)",
        minimum: -10,
        maximum: 10                                               
      },

      interactivityEnabled: false,

      legend: {
        fontColor: "rgb(255, 255, 255)",
      },


      data: [              
        {
            type: "spline",
            xValueType: "dataTime",   
            dataPoints: dpsMx,
            name: "Mx",
            color: "rgb(108, 134, 221)",
            showInLegend: true,
            
        },
        {
            type: "spline",
            xValueType: "dataTime",   
            dataPoints: dpsMxy,
            name: "|Mxy|",
            showInLegend: true,
            color: "rgb(255, 255, 255)",

        }
    ],
});


var pulse = new CanvasJS.Chart("RF_Pulse", {
    backgroundColor: "transparent",
	title:{
		text: ""                                                //title of the graph              
	},

    axisX:{
        title: "time [ms],  Δt = 100ms",
        labelFontSize: 0,                                               //setting it to zero, so it disappears (dont need that here)
        titleFontColor: "rgb(255, 255, 255)",
        valueFormatString: "s.L' s'"
      },

      axisY:{
        title: "Amplitude [T]",
        labelFontSize: 0,
        titleFontColor: "rgb(255, 255, 255)",
        minimum: -5.1,
        maximum: 5.1                                               //setting it to zero, so it disappears (dont need that here)
      },

      interactivityEnabled: false,

      legend: {
        fontColor: "rgb(255, 255, 255)",
      },


      data: [              
        {
            type: "spline",
            xValueType: "dataTime",   
            dataPoints: dpsBxy,
            name: "|Bxy|",
            showInLegend: true,
            color: "rgb(255, 255, 255)",

        }
    ],
});





let xVal = 0;
let yValMx;
let yValMxy;
let yValBxy;


// yValBxy = Bxy;
// yValMx = Mx;
// yValMxy = Mxy;


let dataLength = 700;   
let updateInterval = 20;

let updateChart = function(count){
   count = count || 1;
   
   for(var j = 0; j < count; j++){

    yValBxy = Bxy;
    yValMx = Mx;
    yValMxy = Mxy;

    if(gradient_Mode == true){
        yValMx = MxMean;
        yValMxy = MxyMean;
    }
    
    dpsMx.push({
        y: yValMx,
        x: xVal,
        
    });
    
    dpsMxy.push({
        x: xVal,
        y: yValMxy
    });
    
    dpsBxy.push({
        x: xVal,
        y: yValBxy
    });
    
    xVal = xVal + 100
   }
   
   if(dpsMx.length > dataLength){
    dpsMx.shift();
    dpsMxy.shift();
    dpsBxy.shift();
   }
   //need to deactivate for release
//    var originalLog = console.log;
//     // empty console.log
//     console.log = function() {};

    atomValue.render();
    pulse.render();

    // console.log = originalLog;
}

updateChart(dataLength);
setInterval(function(){
    updateChart();
}, updateInterval)

	
