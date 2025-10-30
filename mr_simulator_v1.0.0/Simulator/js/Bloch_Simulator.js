import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/Addons.js';
import * as dat from 'dat.gui';
import Stats from 'three/examples/jsm/libs/stats.module.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { readSequence } from './sequenz';









//__________________________
//////////////////// General

const renderer = new THREE.WebGLRenderer();
const loader = new GLTFLoader();
const textureLoader = new THREE.TextureLoader();

renderer.shadowMap.enabled = true;
renderer.localClippingEnabled = true;

renderer.setSize(window.innerWidth, window.innerHeight);

document.body.appendChild(renderer.domElement);



const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
    70,
    window.innerWidth / window.innerHeight,
    0.1,
    500
);

// const cameraHelper = new THREE.CameraHelper(camera);
// scene.add(cameraHelper);

camera.position.set(0, 8, 14);

// NOT DONE
// function updateCamera(x, y, z) {
//     camera.position.set(x, y, z);
//     camera.updateProjectionMatrix();
// }

function changeOrbiterPosition(x, y, z) {   
    orbit.target.set(x, y, z); 
    orbit.update(); 
}






const orbit = new OrbitControls(camera, renderer.domElement);
orbit.enablePan = false;                                            //so I cant move with right click
orbit.update();

const axesHelper = new THREE.AxesHelper(10);
scene.add(axesHelper);
axesHelper.visible = false;

// const gridHelper = new THREE.GridHelper(200, 20);
// scene.add(gridHelper);

const clock = new THREE.Clock();    	// get time


// optimizing tools/monitoring
var stats = new Stats();
document.body.appendChild(stats.dom);







//_________________________
//////////////////// Lights
function lights(x, y, z, lightStrength){
    const dLight = new THREE.DirectionalLight(0xFFFFFF, lightStrength);
    scene.add(dLight);

    dLight.position.set(x, y, z);

    dLight.shadow.mapSize.width = 1250;
    dLight.shadow.mapSize.height = 1250;
    dLight.shadow.camera.far = 150;

    dLight.shadow.camera.bottom = -100
    dLight.shadow.camera.top = 100
    dLight.shadow.camera.left = -100
    dLight.shadow.camera.right = 100

    dLight.castShadow = true;
    dLight.angle = 100;

    // Light helpers
    // const dLightHelper = new THREE.DirectionalLightHelper(dLight);
    // scene.add(dLightHelper);

    // const dLightShadowHelper = new THREE.CameraHelper(dLight.shadow.camera);
    // scene.add(dLightShadowHelper);
}

const dLightYAxis = lights(0, 100, 0, 2);
const dLightPlusZAxis = lights(0, 0, 70, 0.2);
const dLightMinusZAxis = lights(0, 0, -70, 0.2);
const dLightPlusXAxis = lights(70, 0, 0, 0.2);
const dLightMinusXAxis = lights(-70, 0, 0, 0.2);












//___________________________
//////////////////// Geometry

///Plane
const planeGeometry = new THREE.PlaneGeometry(120, 120);
const planeMaterial = new THREE.MeshLambertMaterial({
    color: 0xb3cde0,
});

const plane = new THREE.Mesh(planeGeometry, planeMaterial);
scene.add(plane)

plane.rotation.x = -0.5 * Math.PI;
plane.position.set(0, -5, 0)
plane.receiveShadow = true;



/// Arrow for Longitudinal Magnetization
const dir_long = new THREE.Vector3( 0, 1, 0 );
//normalize the direction vector (convert to vector of length 1)
dir_long.normalize();
const origin_long = new THREE.Vector3( 0, 0, 0 );
var length_long = 0;
const hex_long = 0xFF8C00;

const arrow_long = new THREE.ArrowHelper( dir_long, origin_long, length_long, hex_long );
scene.add(arrow_long);
arrow_long.visible = false;

/// Arrow for Transversal Magnetization
const dir_trans = new THREE.Vector3( 1, 0, 0 );
//normalize the direction vector (convert to vector of length 1)
dir_trans.normalize();
const origin_trans = new THREE.Vector3( 0, 0, 0 );
var length_trans = 0;
const hex_trans = 0xFF8C00;

const arrow_trans = new THREE.ArrowHelper( dir_trans, origin_trans, length_trans, hex_trans );
scene.add(arrow_trans);
arrow_trans.visible = false;



/// Pointer ( red ball )
const ballGeometry = new THREE.SphereGeometry(0.25, 15, 15);
const ballMaterial = new THREE.MeshBasicMaterial({
    color: 0xFF0000
});
const ball = new THREE.Mesh(ballGeometry, ballMaterial);
scene.add(ball);



/// Line
let lineToRemove = null;
let points = [];
let line_length = 0;
function line_helper(vector){
    const lineMaterial = new THREE.LineBasicMaterial({
    color: 0xFF0000
    });

    points.push(vector);

    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
    const line = new THREE.Line( lineGeometry, lineMaterial);

    while (points.length > line_length){
        points.shift();
    }


    scene.add(line);

    if (lineToRemove != null){
        scene.remove(lineToRemove);
    }

    lineToRemove = line;
}




// clipping planes
const localPlanes = [
    new THREE.Plane( new THREE.Vector3( 0, -1, 0 ), 120 ),
    new THREE.Plane( new THREE.Vector3( 0, 1, 0 ), 10 )
]
const helpers = new THREE.Group();
helpers.add( new THREE.PlaneHelper( localPlanes[ 0 ], 60, 0xff0000 ) );
helpers.add( new THREE.PlaneHelper( localPlanes[ 1 ], 60, 0x00ff00 ) );
helpers.visible = true;
//scene.add( helpers );

// Update the clipping planes based on the current yPlane value
function updatePlane(){ 
    if(Math.round(localPlanes[0].constant*10)/10 != (yPlane+2.5)){
        if(Math.round(localPlanes[0].constant*10)/10 > (yPlane+2.5)){
            localPlanes[0].constant -= 0.5;
        }
        else{
            localPlanes[0].constant += 0.5;
        }
    }

    if(Math.round(localPlanes[1].constant*10)/10 != (-yPlane+2.5)){
        if(Math.round(localPlanes[1].constant*10)/10 < (-yPlane+2.5)){
            localPlanes[1].constant += 0.5;
        }
        else{
            localPlanes[1].constant -= 0.5;
        }
    }
        
        
   
}



/// Head 
let headMesh;
let headMesh2;
let geometry;

const url = new URL('../models/LeePerrySmith.glb', import.meta.url).href;


const head = new Promise(function(resolve, reject) {
    loader.load(
        url,
        function(gltf) {
            console.log('Model loaded');
            resolve(gltf);
        },
        undefined,
        function(error) {
            console.error('failure loading model:', error);
            reject(error);
        }
    );
});

head.then(
    function(gltf) {
        console.log('Promise "geometry" achieved');
        // Verarbeiten Sie hier das geladene Modell
        geometry = gltf.scene.children[0].geometry;
    },
    function(error) {
        console.error('Error promise function:', error);
    }
);

head.then(
    function(gltf) {
        console.log('Promise "headMesh" achieved');
        // Verarbeiten Sie hier das geladene Modell
        const headGeometry = gltf.scene.children[0].geometry;
        const headMaterial = new THREE.MeshLambertMaterial({
            color: 0xFFFFFF,
            wireframe: true,
            transparent: true,
            opacity: 0.15
        });
        headMesh = new THREE.Mesh(headGeometry, headMaterial);

        headMesh.visible = false;
        headMesh.scale.set(15, 15, 15);
        headMesh.position.y = 51;

        scene.add(headMesh);
    },
    function(error) {
        console.error('Error promise function:', error);
    }
);

head.then(
    function(gltf) {
        console.log('Promise "headMesh2" achieved');
        // Verarbeiten Sie hier das geladene Modell
        const headGeometry = gltf.scene.children[0].geometry;
        const headMaterial = new THREE.MeshLambertMaterial({
            color: 0xFFFFFF,
            //wireframe: true,
            clippingPlanes: localPlanes
        });
        headMesh2 = new THREE.Mesh(headGeometry, headMaterial);

        headMesh2.visible = false;
        headMesh2.scale.set(15, 15, 15);
        headMesh2.position.y = 51;

        scene.add(headMesh2);
    },
    function(error) {
        console.error('Error promise function:', error);
    }
);


/// Atom
let atomLength = 5;
let atom 

function createAtom(shape) {
    const geo = new THREE.CapsuleGeometry(0.2, atomLength, 1, 12);
    geo.translate(0, atomLength / 2, 0);
    geo.rotateX(Math.PI * 0.5);

    const mat = new THREE.MeshLambertMaterial({
        color: 0xFFEBCD,
    });

    let mesh;

    switch(shape){
        case 'cube':
            console.log('--->Atoms in Cube shape')

            mesh = new THREE.InstancedMesh(geo, mat, 343);
            scene.add(mesh);
            break;

        case 'plane':
            console.log('--->Atoms in Plane shape');
            mesh = new THREE.InstancedMesh(geo, mat, 49);
            break;

        case 'single':
            console.log('--->Only a Single Atom');

            mesh  = new THREE.InstancedMesh(geo, mat, 1);

    }
    scene.add(mesh);
    mesh.castShadow = true;

    mesh.geometry.computeBoundingSphere();
    mesh.frustumCulled = false;

    return { mesh, mat };
}

function updateInstanceMesh(){
    console.log('!!!Updating Instance Mesh!!!');
    scene.remove(atom.mesh);

    atom = createAtom(currentShape);
    scene.add(atom.mesh);
}



/// Sphere
const sphereGeometry = new THREE.SphereGeometry(atomLength, 12, 12);
const sphereMaterial = new THREE.MeshBasicMaterial({
    color: 0xFFFFFF,
    transparent: true,
    wireframe: true,
    opacity: 0.25
})
const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
scene.add(sphere);
sphere.visible = false;

















//__________________________________
////////// Button/Animation
/// NOT DONE YET (can add many other functions)
//degree_button --> how much degree
//button_type --> what type button for example: 0 for Equilibrium, 1 for rotation, 2 for Single Mode and 3 for Gradient mode

let starttime = 0;
export let single_Mode = false;
export let gradient_Mode = false;
let tutorial_Mode = true;

export function buttonEvents(degree_button, button_type){


    switch (button_type){

        case 0:
            // remvove last line
            scene.remove(lineToRemove);


            // reset Values
            MxyMean = 0;
            MxMean = 0;
            T = 0;
            currentM = [0, 0, atomLength];
            localPlanes[0].constant = 120;
            localPlanes[1].constant = 10;

            if  (gradient_Mode === true){
                currentShape = 'cube';
                updateInstanceMesh();
                resetParameters();
            }
            
            
            
            break;

        //button action
        case 1:
            //check if B1 or B1freq is zero            
            if(B1 === 0 || B1freq === 0){
                alert("Invalid B1 or B1freq (should != 0)")
            }

            //activate pulse
            else{
                starttime = clock.elapsedTime;
                
                if(gradient_Mode === true){
                    currentShape = 'cube';
                    sliceSelectionSwitch = true; 
                }

                pulseTypeSelectionTau(degree_button);
            }


            break;


        case 2:
            console.log('____________');
            console.log('Single Mode activated');
            T = 0;

            

            //remove/add objects
            if (gradient_Mode === true){
                scene.remove(atom.mesh);
                headMesh.visible = false;
                headMesh2.visible = false;
                scene.add(ball);

                atomLength = 5;
                atom = createAtom('single');
                camera.position.set(0, 8, 14);
                changeOrbiterPosition(0, 0, 0); 
            }




            //update mode values
            gradient_Mode = false;
            tutorial_Mode = false;
            single_Mode = true;
            visualizer_switch();

            //reset values
            M0 = atomLength; // Equilibrium magnetization
            initialM = [0.0, 0.0, atomLength]; // Initial magnetization (the starting point)
            currentM = initialM;   
            

            //reset folder visibility
            //basicParameterFolder.show();
            //relaxationFolder.show();
            rfPulseFolder.show();


            break;


        case 3:
            console.log('____________');
            console.log('Gradient Mode activated');
            T = 0;


            //remove last objects
            if (single_Mode === true || tutorial_Mode === true){
                scene.remove(atom.mesh);
                scene.remove(lineToRemove);
                scene.remove(ball);
            }


            //update mode values
            single_Mode = false;
            tutorial_Mode = false;
            gradient_Mode = true;
            
            visualizer_switch();

            //reset values
            resetParameters();
            atomLength = 2.5;
            M0 = atomLength; // Equilibrium magnetization
            initialM = [0.0, 0.0, atomLength]; // Initial magnetization (the starting point)
            currentM = initialM;
            currentShape = 'cube';
            localPlanes[0].constant = 120;
            localPlanes[1].constant = 10;
            sphere.visible = false;
            axesHelper.visible = false;
            arrow_long.visible = false;
            arrow_trans.visible = false;
            camera.position.set(0, 73, 65);
            changeOrbiterPosition(0, 65, 0); 

            //reset folder visibility
            //basicParameterFolder.show();
            relaxationFolder.show();
            rfPulseFolder.show();



            //create objects
            atom = createAtom('cube');
            

            break;


        case 4:
            console.log('____________');
            console.log('Tutorial Mode activated');


            //remove/add objects and reset values (only if from gradient to tutorial)
            if (gradient_Mode === true){
                scene.remove(atom.mesh);
                headMesh.visible = false;
                headMesh2.visible = false;
                atomLength = 5;
                atom = createAtom('single');
                scene.add(ball);
                camera.position.set(0, 8, 14);
                changeOrbiterPosition(0, 0, 0); 

            }
            else if (tutorial_Mode === true){
                atom = createAtom('single');
            }
            

            //update mode values
            gradient_Mode = false;
            tutorial_Mode = true;
            single_Mode = false;
            visualizer_switch();

            //reset values
            M0 = atomLength; // Equilibrium magnetization
            initialM = [0.0, 0.0, atomLength]; // Initial magnetization (the starting point)
            currentM = initialM;
            

            //reset folder visibility
            //basicParameterFolder.hide();
            //relaxationFolder.hide();
            rfPulseFolder.hide();

            
    }
}















//____________
////////// GUI
const gui = new dat.GUI();
const options = {
    Sphere: false,
    Magnetization_Arrows: false,
    Axes: false,
    line_length: 300,
    shape: 'cube',
    B0: 2.5,
    Relaxation: false,
    Pulse_type: 'Square',
    B1: 0,
    B1freq: 0,
    T1_value: 9.0,
    T2_value: 9.0

};

const visualizerFolderSingle = gui.addFolder('Single Atom Visualizer');
visualizerFolderSingle.add(options, 'Sphere').onChange(function(e){
    sphere.visible = e;
});
visualizerFolderSingle.add(options, 'Magnetization_Arrows').onChange(function(e){
    arrow_long.visible = e;
    arrow_trans.visible = e;
});
visualizerFolderSingle.add(options, 'Axes').onChange(function(e){
    axesHelper.visible = e;
});
const lineLengthValue = visualizerFolderSingle.add(options, 'line_length', 0, 2500, 5);
visualizerFolderSingle.open();

const visualizerFolderGradient = gui.addFolder('Gradient Mode Visualizer');
const gradientShape = visualizerFolderGradient.add(options,'shape', ['cube', 'head'])
visualizerFolderGradient.open();


const basicParameterFolder = gui.addFolder('Basic Parameter');
const B0Value = basicParameterFolder.add(options, 'B0', 0.0, 5.0).name("B0 [T]");
const relaxationSwitch = basicParameterFolder.add(options, 'Relaxation').onChange(function(e){
    relaxation = e;
});
basicParameterFolder.open();



const relaxationFolder = gui.addFolder("Relaxation");
const t1_relaxation = relaxationFolder.add(options, 'T1_value', 1, 9).name("T1 [s]");
const t2_relaxation = relaxationFolder.add(options, 'T2_value', 1, 9).name("T2 [s]");
relaxationFolder.open();



const rfPulseFolder = gui.addFolder("RF-Pulse configuration");
const pulseType = rfPulseFolder.add(options,'Pulse_type', ['Square', 'Sinc'])
const B1Value = rfPulseFolder.add(options,'B1', 0.0, 5.0, 0.1).name("B1 [T]");
const B1FreqValue = rfPulseFolder.add(options, 'B1freq', 0.0, 11.0, 0.1).name("B1freq [Hz]");
rfPulseFolder.open();


//// GUI Tooltip
function showTooltip(event, message, labelElement) {
    const tooltip = document.createElement('div');
    tooltip.style.position = 'absolute';
    tooltip.style.background = 'rgba(0, 0, 0, 0.7)';
    tooltip.style.color = 'white';
    tooltip.style.padding = '5px';
    tooltip.style.borderRadius = '5px';
    tooltip.style.fontSize = '16px';
    tooltip.style.pointerEvents = 'none';
    tooltip.style.maxWidth = '200px'; 
    tooltip.style.wordWrap = 'break-word'; 
    tooltip.style.wordBreak = 'break-word';
    tooltip.textContent = message;

    document.body.appendChild(tooltip);

    // position left from label
    const labelRect = labelElement.getBoundingClientRect();
    const tooltipWidth = tooltip.offsetWidth;

    tooltip.style.top = `${labelRect.top + window.scrollY}px`; // vertikal position
    tooltip.style.left = `${labelRect.left + window.scrollX - tooltipWidth - 10}px`; // horizont position

    // delete div if mouseout
    function removeTooltip() {
        if (document.body.contains(tooltip)) {
            document.body.removeChild(tooltip);
        }
    }

    event.target.addEventListener('mouseout', removeTooltip);
}

// get label
function addTooltipOnLabel(controller, message) {
    const label = controller.domElement.parentElement.querySelector('span');
    if (label) {
        label.addEventListener('mouseover', (event) => {
            showTooltip(event, message, label);
        });
    } else {
        console.warn('Label not found!');
    }
}

addTooltipOnLabel(B0Value, 'Constant, homogeneous magnetic field');
addTooltipOnLabel(relaxationSwitch, 'Activate/Deactivate process in which the spin relaxes back to equilibrium');
addTooltipOnLabel(pulseType, 'Select RF-Pulse Type');
addTooltipOnLabel(B1Value, 'Adjust the amplitude for the RF-Pulse');
addTooltipOnLabel(B1FreqValue, 'Adjust the frequency of the RF pulse. It starts at the Larmor frequency (determined by B0) and increases in steps of 0.5 Hz (only 7 times).');
addTooltipOnLabel(t1_relaxation, 'Time that is needed for 63% of the protons to realign with the magnetic field')
addTooltipOnLabel(t2_relaxation, 'Time that is needed to dephase to 37% of the original value')


//// GUI Functions
let relaxation = false;      // important for gui


function t1_t2_gui_switch(){
    if (relaxation == true){
        relaxationFolder.show(options.T1_value);
        relaxationFolder.show(options.T1_value);
    }
    else{
        relaxationFolder.hide(options.T1_value);
        relaxationFolder.hide(options.T2_value);
    }
}


// switching between with relaxation and without relaxation
function relaxation_switch(dt, currentM, B, T1, T2){

    if (relaxation === false){
        t1_t2_gui_switch();
        return rungeKuttaStep(blochEquationsNoRelaxation, currentM, dt, [gamma, B, M0]);
    }

    else{
        t1_t2_gui_switch();
        return rungeKuttaStep(blochEquationsWithRelaxation, currentM, dt, [gamma, B, M0, T1, T2]);
    }
};


// make sure that T2 is not greater than T1
function relaxation_validation(){

    t1_relaxation.onChange(function(value){
        if(options.T1_value<= options.T2_value){
            options.T2_value = value;
            t2_relaxation.updateDisplay();
        }
    })

    t2_relaxation.onChange(function(value){
        if(options.T1_value<= options.T2_value){
            options.T1_value = value;
            t1_relaxation.updateDisplay();
        }
    })
}

t1_relaxation.onChange(function(value){
    relaxation_validation();
});

t2_relaxation.onChange(function(value){
    relaxation_validation();
});


// switch between Square and Sinc pulse (for the tau calculation)
function pulseTypeSelectionTau(degree_button){

    switch(options.Pulse_type){

        case 'Square':
            T = degreeToRad(degree_button) / (gamma * B1);
            console.log('--->Here is the Square Pulse');
            break;

        case 'Sinc': //B1 value is important for the sinc pulse, how much it will flip
            T = 5; //five means: five "waves"
            console.log('--->Here is the sinc pulse');

    }
}

function visualizer_switch(){
    if(gradient_Mode === true){
        visualizerFolderGradient.show();
        visualizerFolderSingle.hide();
    }
    else if(single_Mode === true){
        visualizerFolderGradient.hide();
        visualizerFolderSingle.show();
    }
    else{
        visualizerFolderGradient.hide();
        visualizerFolderSingle.show();
    }

}









//_______________________________
////////// Simple Calculations
function radToDegree(rad){
    var degree = (rad) * (180 / Math.PI);
    return degree
};

function degreeToRad(degree){
    var rad = (degree) * (Math.PI / 180)
    return rad
};











//________________________
////////// Bloch Equations

// Import math.js for numerical calculations (https://mathjs.org/)
const math = require('mathjs');





//// Functions
// Define the Bloch equations with relaxation
function blochEquationsWithRelaxation(M, gamma, B0, M0, T1, T2) {
  const [Mx, My, Mz] = M;
  const [Bx, By, Bz] = B0;

  const dMx_dt = gamma * (My * Bz - Mz * By) - Mx / T2;
  const dMy_dt = gamma * (Mz * Bx - Mx * Bz) - My / T2;
  const dMz_dt = gamma * (Mx * By - My * Bx) + (M0 - Mz) / T1;

  return [dMx_dt, dMy_dt, dMz_dt];
}

// Define the Bloch equations without relaxation
function blochEquationsNoRelaxation(M, gamma, B0) {
    const [Mx, My, Mz] = M;
    const [Bx, By, Bz] = B0;

    const dMx_dt = gamma * (My * Bz - Mz * By);
    const dMy_dt = gamma * (Mz * Bx - Mx * Bz);
    const dMz_dt = gamma * (Mx * By - My * Bx);

    return [dMx_dt, dMy_dt, dMz_dt];
  }

// Runge-Kutta method to solve ODEs
function rungeKuttaStep(f, y, dt, params) {
    const k1 = math.multiply(f(y, ...params), dt);
    const k2 = math.multiply(f(math.add(y, math.multiply(k1, 0.5)), ...params), dt);
    const k3 = math.multiply(f(math.add(y, math.multiply(k2, 0.5)), ...params), dt);
    const k4 = math.multiply(f(math.add(y, k3), ...params), dt);

    return math.add(y, math.divide(math.add(k1, math.multiply(k2, 2), math.multiply(k3, 2), k4), 6));
  }










//// Parameters



// dummies for the gui
//values here zero, will asigned to the value of gui in the animation function
let B0 = 0.0;
let T1 = 0.0; // Longitudinal relaxation time in seconds
let T2 = 0.0; // Transverse relaxation time in seconds
let B1 = 0.0;
let B1freq = 0.0;

//dummies for parameters
let B = 0;
let T =  0; // time to reach for example the 90 degree



const gamma = 1;  // gamma for B0

let M0 = atomLength; // Equilibrium magnetization
let initialM = [0.0, 0.0, atomLength]; // Initial magnetization (the starting point)


// Values
export let Mx = 0;
export let My = 0;
export let Mz = 0;
export let Mxy = 0;
let currentM = initialM; // Magnetization state
export let Bxy = 0;



// Values for Gradient Mode
let currentShape = 'cube';
let gradientZ = 0.1;
let gradienty = 0;
let gradientx = 0.5;
let yPlane = 0; //which plane is selected
let gradientCurrentM = new Array();
let gradientCurrentMIndex = 0;

export let MxMean = 0;
export let MxyMean = 0;


// Time value
let lastTime = 0; // Last recorded time for calculations


//Sequence
export function sequence_reader(file) { //?????????????????
    console.log("final destination");
    var readed_sequence = readSequence(file);
    //readed_sequence.then(readed_sequence);
    console.log(readed_sequence);
    console.log(readed_sequence[0]);
}







// B dependent on time
function B_RF_Field_Square(elapsedTime, B0, B1, pulseDuration){
    if (elapsedTime < pulseDuration) {
        
        const omega = gamma * B1freq
        
        // RF pulse active
        return [B1 * Math.cos(omega * elapsedTime),
                -B1 * Math.sin(omega * elapsedTime),
                B0];
      } else {
        // After the RF pulse
        return [0,
                0,
                B0];
      }
}




function B_RF_Field_Sinc(elapsedTime, B0, B1, pulseDuration) {

    if (elapsedTime < pulseDuration) {
        let time = elapsedTime - starttime;
        const omega = gamma * B1freq
        
        const sincValue = Math.sin(Math.PI * (time - T/2)) / (Math.PI * (time - T/2));


        return [B1 * Math.cos(omega * time) * sincValue,
                -B1 * Math.sin(omega * time) * sincValue,
                B0];

    } else {
        return [0, 0, B0];
    }
}





function updateB(elapsedTime){
    const targetTime = starttime + T
    
    switch(options.Pulse_type){
        case 'Square':
            return B_RF_Field_Square(elapsedTime, B0, B1, targetTime);
            break;
        case 'Sinc':
            return B_RF_Field_Sinc(elapsedTime, B0, B1, targetTime);
    }

}



function cubeCurrentM(axis, start, end, gradient, index, elapsedTime, dt){
    for(axis = start; axis<=end; axis += 5){
        t1_t2_gui_switch();
        B0 = options.B0 + gradient * axis - 6.5;
        B = updateB(elapsedTime);
        Bxy = Math.sqrt(B[0] ** 2 + B[1] ** 2); //Bxy for the Graph


        sliceSelection(B0, atom, axis, index); //set B at Equilibrium, so no pulse if B0 != B1Freq
        
        
        // let currentM = relaxation_switch(dt, gradientCurrentM[index], B, T1, T2);
        // gradientCurrentM[index] = currentM;
        index++;
    };
    if(currentShape === 'cube' && sliceSelectionSwitch === true && yPlane!=0){
        currentShape = 'plane';
    }
    sliceSelectionSwitch = false;
}



function planeCurrentM(gradient, elapsedTime, dt){
    
    B0 = options.B0 + gradient * yPlane - 6.5;
    B1freq = options.B1freq;
    B = updateB(elapsedTime);
    Bxy = Math.sqrt(B[0] ** 2 + B[1] ** 2); //Bxy for the Graph
    currentM = relaxation_switch(dt, currentM, B, T1, T2);
    gradientCurrentM[gradientCurrentMIndex] = currentM;
    return currentM
}



// function just for the gradient mode to fill the M List with intial M values
function resetParameters(){
    gradientCurrentM = new Array(13).fill([0, 0, 2.5]);
    Mx = 0;
    My = 0;
    Mz = 0;
    Mxy = 0;
    MxMean = 0;
    MxyMean = 0;
    Bxy = 0;
    yPlane = 0;
}







/// Gradient Functions
let sliceSelectionSwitch = false;
function sliceSelection(B0, obj, y, index){
    // round to one decimal place
    B0 = Math.round(B0 * 10)/10 
    let B1freqRounded = (Math.round(options.B1freq * 10)/10);
    
    switch(sliceSelectionSwitch){
        case true:
            if(B0 == B1freqRounded){
                currentM = gradientCurrentM[index];
                scene.remove(atom.mesh);
                yPlane = y; 
                gradientCurrentMIndex = index;

                currentShape = 'plane';
                updateInstanceMesh();
                
            }       
    } 
}










let animationID;
// Animate function
function animate() {
    
    renderer.render(scene, camera);

    //perfomance monitoring
    //console.log(renderer.info.render);
    stats.update();

    const elapsedTime = clock.getElapsedTime(); // Get the elapsed time in seconds
    
    const dt = Math.min(elapsedTime - lastTime, 0.1); // Time step for this frame

    


    // Update the parameters from the GUI
    T1 = options.T1_value;
    T2 = options.T2_value;
    B0 = options.B0;
    B1 = options.B1;
    B1freq = options.B1freq;
    line_length = options.line_length;
    

    if (dt > 0) {

        let targetPosition

        if (gradient_Mode === true){

            
            let index = 0;
            let gradientIndex = 0;
            
            switch(options.shape){
                case 'cube':
                    headMesh.visible = false;
                    headMesh2.visible = false;
                    break;
                case 'head':
                    headMesh.visible = true;
                    headMesh2.visible = true;
                    break;
            }

            switch(currentShape){

                case 'cube':

                    cubeCurrentM('y', 65, 95, gradientZ, gradientIndex, elapsedTime, dt);
                    if(currentShape === 'cube'){
                        for (let y = 65; y<=95; y += 5) {
                        for (let x = -15; x<=15; x += 5){
                            for (let z = -15; z<=15; z += 5){

                                const dummy = new THREE.Object3D();
                                dummy.position.set(x, y, z);

                                let Mx = gradientCurrentM[gradientIndex][0];
                                let My = gradientCurrentM[gradientIndex][1];
                                let Mz = gradientCurrentM[gradientIndex][2];


                                targetPosition = new THREE.Vector3(Mx + x, Mz + y, My + z);
                                dummy.lookAt(targetPosition);
                                dummy.updateMatrix();
                                atom.mesh.setMatrixAt(index, dummy.matrix);
                                index++
                            }
                        }
                        gradientIndex++;

                    }
                    }
                    
                    break;


                case 'plane':
                    
                    updatePlane();
                    let currentM = planeCurrentM(gradientZ, elapsedTime, dt);
                    
                    let MxMeanTotal = 0;
                    let MxyMeanTotal = 0;

                    for (let x = -15; x<=15; x += 5){
                        for (let z = -15; z<=15; z += 5){

                            const dummy = new THREE.Object3D();
                            dummy.position.set(x, yPlane, z);

                            let Mx = currentM[0];
                            let My = currentM[1];
                            let Mz = currentM[2]; 

                            MxMeanTotal += Mx;
                            MxyMeanTotal += math.sqrt(Mx**2 + My**2) 

                            targetPosition = new THREE.Vector3(Mx + x, Mz + yPlane, My + z);
                            dummy.lookAt(targetPosition);
                            dummy.updateMatrix();
                            atom.mesh.setMatrixAt(index, dummy.matrix);
                            index++
                        }
                        gradientIndex++
                    }
                    MxMean = (MxMeanTotal/49);
                    MxyMean = (MxyMeanTotal/49);      
            }
            atom.mesh.instanceMatrix.needsUpdate = true;
        }
        



        else if (single_Mode === true){


            B0 = options.B0
            B = updateB(elapsedTime);
            Bxy = Math.sqrt(B[0]**2 + B[1]**2);

            // solving bloch equation
            currentM = relaxation_switch(dt, currentM, B, T1, T2);

            Mx = currentM[0];
            My = currentM[1];
            Mz = currentM[2];
            Mxy = Math.sqrt(Mx**2 + My**2);

            targetPosition = new THREE.Vector3(Mx, Mz, My);

            // Updating the length from the magnetization arrows
            let length_long = Mz;
            arrow_long.setLength(length_long);
            let length_trans = Mxy;
            arrow_trans.setLength(length_trans);

            const dummy = new THREE.Object3D();
            dummy.position.set(0, 0, 0);
            dummy.lookAt(targetPosition);
            dummy.updateMatrix();
            atom.mesh.setMatrixAt(0, dummy.matrix);
            atom.mesh.instanceMatrix.needsUpdate = true;


            line_helper(targetPosition);  //--> line_helper with limited points

            ball.position.set(Mx, Mz, My);
        }

        else if(tutorial_Mode === true){
            B1 = 0.3;
            B1freq = options.B0;
            B = updateB(elapsedTime);
            Bxy = Math.sqrt(B[0]**2 + B[1]**2);


            currentM = relaxation_switch(dt, currentM, B, T1, T2);

            Mx = currentM[0];
            My = currentM[1];
            Mz = currentM[2];
            Mxy = Math.sqrt(Mx**2 + My**2);

            targetPosition = new THREE.Vector3(Mx, Mz, My);

            // Updating the length from the magnetization arrows
            let length_long = Mz;
            arrow_long.setLength(length_long);
            let length_trans = Mxy;
            arrow_trans.setLength(length_trans);

            const dummy = new THREE.Object3D();
            dummy.position.set(0, 0, 0);
            dummy.lookAt(targetPosition);
            dummy.updateMatrix();
            atom.mesh.setMatrixAt(0, dummy.matrix);
            atom.mesh.instanceMatrix.needsUpdate = true;


            line_helper(targetPosition);  //--> line_helper with limited points

            ball.position.set(Mx, Mz, My);
            
        }
    }
        // Update lastTime
        lastTime = elapsedTime;
        animationID = requestAnimationFrame(animate);

}

animate();






window.addEventListener('resize', () => {
    // set new size
    renderer.setSize(window.innerWidth, window.innerHeight);

    // new ratio
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
});




//_______________________________
///// To-Do-List (fixing things)

// --> switch camera position, if in gradientmode (switch to yPlane if slice selected)

// --> calculation for B1 in sinc mode for the buttons

// change color of atoms

// --> add wait/promise function for gltf loader


























