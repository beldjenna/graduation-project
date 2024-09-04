#include<SPI.h>
#include<SD.h>
#include<FreeRTOS.h>
#include<task.h>
#include<JPEGDecoder.h>
#include<string>

using namespace std;


// Define a file object
static File imgFile;

// variable to store the image name
char imgName[20];

// Define task handles
TaskHandle_t imgTaskHandle;
TaskHandle_t auxTaskHandle;

// Define the synchronisation marker
const uint32_t syncMarker = 0x1ACFFC1D; // at the begining of each frame 

// Define the desired length segment(1024)
size_t LSEGMENT;

// Define the structure for the frame primary header
struct PrimaryFrameHeader{
  uint16_t frameIdentification;
  uint8_t masterChannelFrameCount;
  uint8_t virtualChannelFrameCount;
  uint16_t frameDataFieldStatus;
};

// Define the structure for the packet Header
struct PacketHeader{
  uint16_t packetIdentification;
  uint16_t packetSequenceControl;
  uint16_t packetLength;
};

// Define the structure for the auxialiary data 
struct AuxiliaryData{
  float velocity[3]; //velocity(x,y,z)
  float attitude[4]; // q0,q1,q2,q3 in the range [0,1]
  int gpsTime[2];  
  float position[3];
};

void sendAuxData(void * pvParam)
{
  // Define and populate the auxialiary data
  AuxiliaryData auxData;
  auxData.velocity[0] = 0.21565848; // Example
  auxData.velocity[1] = 7.125655144; // Example
  auxData.velocity[2] = 12.213232563; // Example
  
  // satellite attitude
  auxData.attitude[0] = random(0,100.0) / 100.0;
  auxData.attitude[1] = random(0,100.0) / 100.0;
  auxData.attitude[2] = random(0,100.0) / 100.0;
  auxData.attitude[3] = random(0,100.0) / 100.0;

  // Example GPS time
  auxData.gpsTime[0] = 2318; // Example GPS number of weeks
  auxData.gpsTime[1] = 124607; // Example GPS time of week (in seconds)

  // Example values of gps position
  auxData.position[0] = 0.2145888;
  auxData.position[1] = 1.258886;
  auxData.position[2] = 2.255545445;

  // Send the auxiliary data 
  Serial.write((char*)&auxData, sizeof(auxData));

  // Delete the auxiliary data task
  vTaskDelete(auxTaskHandle);

}


void frameHeader(PrimaryFrameHeader &primHead)
{
  //frame primary header fields
  //fill in the frame identification field
  uint16_t versionNo = 1;
  uint16_t scID = 5; //example
  uint16_t virtChanID = 3; //example
  uint16_t operatControl = 0;
  primHead.frameIdentification = (versionNo << 14) | (scID << 4) | (virtChanID << 1) | operatControl;

  //Fill in the master channel frame count field
  primHead.masterChannelFrameCount = 1;

  //Fill in the virtual channel frame count field
  primHead.virtualChannelFrameCount = 1;

  // Fill in the frame data field status field
  uint16_t secHeadFlag = 0;
  uint16_t syncFlag = 0;
  uint16_t packetOrderFlag = 1;
  uint16_t segmentLengthID = 0b10; // 1024 bytes
  uint16_t firstHeadPointer = 5;//example
  primHead.frameDataFieldStatus = (secHeadFlag << 15) | (syncFlag << 14) | (packetOrderFlag << 13) | (segmentLengthID << 11) | firstHeadPointer;

}


void packetHeader(PacketHeader &header, size_t &segmentSize, uint16_t &segmentationFlags, uint16_t &sourceSequenceCount)
{
  // packet header fields
  // Fill in the packet identification field
  uint16_t versionNumber = 2;
  uint16_t type = 0;
  uint16_t dataFieldHeaderFlags = 0;
  uint16_t applicationProcessID = 1400;
  header.packetIdentification = (versionNumber << 13) | (type << 12) | (dataFieldHeaderFlags << 11) | applicationProcessID;

  // Fill in the packet sequence control field
  header.packetSequenceControl = (segmentationFlags << 14) | (sourceSequenceCount);

  // Fill in the packet length field
  header.packetLength = (segmentSize - 1);
}

void readLine(size_t &LSEGMENT, const char *imgName)
{
  if (JpegDec.decodeFile(imgName) == 0){
    Serial.println("Failed to open image file or decode it!");
  }
  // get the width
  int width = JpegDec.width;

  // LSEGMENT
  LSEGMENT = width *3; // 3 bytes per pixel
  
}



void encapsulateImage(void * pvParam)
{
  // Create the primary frame header
  PrimaryFrameHeader primHead;

  // Create packet header
  PacketHeader header;

  // Declare the sub-fields of the packet sequence control field
  uint16_t segmentationFlags;
  uint16_t sourceSequenceCount;

  size_t imgSize;//the size of the image
  int numSegments;//the number of segments

  //Open the image file for reading 
  imgFile = SD.open(imgName, FILE_READ);

  
  if(imgFile == true){
    imgSize = imgFile.size();//returns the size of the image in bytes
    readLine(LSEGMENT, imgName);
    
    //Determine the number of segments
    numSegments = (imgSize + LSEGMENT - 1) / LSEGMENT;

  }else{
    Serial.println("Error opening the image");
  }

  // Send the number of segments 
  Serial.write((char*)&numSegments, sizeof(numSegments));

  //write the packet
  for (int i = 0; i < numSegments; i++)
  {
    // Calculate the size of each segment
    size_t segmentSize = (i == numSegments - 1) ? (imgSize % LSEGMENT) : LSEGMENT;

    // the segmentation flags sub-field
    if(i == 0){
      segmentationFlags = 0b01;// First segment
    }else if (i == (numSegments -1) ){
      segmentationFlags = 0b10;// Last segment
    }else{
      segmentationFlags = 0b00;// Continuation segment
    }
    
    // The source sequence count sub-field
    sourceSequenceCount = i;

    // Setup the frame headers 
    frameHeader(primHead);

    // Setup the packet header 
    packetHeader(header,segmentSize,segmentationFlags,sourceSequenceCount);


    // Read segment data from image file
    char buffer[LSEGMENT];
    size_t bytesRead = imgFile.read(buffer, segmentSize);

    // Send the synchronisation marker
    Serial.write((char*)&syncMarker, sizeof(syncMarker));
    

    // Send the primary frame header
    Serial.write((char*)&primHead, sizeof(primHead));
    

    // Send the packet header 
    Serial.write((char*)&header, sizeof(header));

    // Send segment data
    Serial.write(buffer, bytesRead);
   

    // Create the auxiliary data task
    xTaskCreate(sendAuxData, (const portCHAR *)"AuxDataTask", 400, NULL, 2, &auxTaskHandle);


    // Wait time between each frame
    vTaskDelay(150);
    

  }
  
  imgFile.close();
  vTaskDelete(imgTaskHandle);
  
}


void setup()
{
  Serial.begin(9600);

  if(!SD.begin(4)) {//CS pin
    Serial.println("Initialization failed, or SDcard not present");
    while(1);
  }
  // Serial.println("\nInitialization done");

  // Create the image task
  // xTaskCreate(encapsulateImage, (const portCHAR *)"encapsulation", 800, &imgFile, 1, &imgTaskHandle);
  vTaskStartScheduler();

  Serial.println("failed to create the schedular");
  while(1);

}

void loop()
{
  if (Serial.available() > 0){
    char choice = Serial.read();

    switch(choice)
    {
      case '1':
        delay(1000);
        strcpy(imgName, "oran.jpg");
        xTaskCreate(encapsulateImage, (const portCHAR *)"encapsulation", 800, &imgFile, 1, &imgTaskHandle);
        break;


      case '2':
        delay(1000);
        strcpy(imgName, "france.jpg");
        xTaskCreate(encapsulateImage, (const portCHAR *)"encapsulation", 800, &imgFile, 1, &imgTaskHandle);
        break;


      case '3':
        delay(1000);
        strcpy(imgName, "cairo.jpg");
        xTaskCreate(encapsulateImage, (const portCHAR *)"encapsulation", 800, &imgFile, 1, &imgTaskHandle);
        break;

      default:
        break;
    }

    // delay(20000);
  }



  

  

}