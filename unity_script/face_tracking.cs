// Receive head-pose over UDP and rotate the camera.
using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

public class HeadPoseReceiverForCamera : MonoBehaviour
{
    [Header("Network Settings")]
    public int listenPort = 9999;      // same port as Python sender

    private UdpClient udpClient;
    private Thread recvThread;
    private bool isRunning = true;

    // latest angles from Python
    private float rollZ = 0f;
    private float pitchY = 0f;
    private float yawX = 0f;

    [Header("Rotation Settings")]
    public float threshold = 30f;      // deg: start auto-spin if exceeded
    public float spinSpeed = 30f;      // deg/s during auto-spin

    // accumulated local Euler angles
    private float currentX = 0f;
    private float currentY = 0f;
    private float currentZ = 0f;

    // auto-spin state per axis
    private bool isSpinningX, isSpinningXPos;
    private float offsetX;
    private bool isSpinningY, isSpinningYPos;
    private float offsetY;
    private bool isSpinningZ, isSpinningZPos;
    private float offsetZ;

    void Start()
    {
        udpClient = new UdpClient(listenPort);
        recvThread = new Thread(ReceiveLoop) { IsBackground = true };
        recvThread.Start();
    }

    void Update()
    {
        // X axis (pitch)
        currentX = SpinWithOffsetLogic(
            sensorVal: pitchY,
            ref isSpinningX, ref isSpinningXPos, ref offsetX, currentX);

        // Y axis (yaw → Unity −Y)
        currentY = SpinWithOffsetLogic(
            sensorVal: -yawX,
            ref isSpinningY, ref isSpinningYPos, ref offsetY, currentY);

        // Z axis (roll → Unity −Z)
        currentZ = SpinWithOffsetLogic(
            sensorVal: -rollZ,
            ref isSpinningZ, ref isSpinningZPos, ref offsetZ, currentZ);

        // apply rotation
        transform.localEulerAngles = new Vector3(currentX, currentY, currentZ);
    }

    /// Auto-spin when |sensorVal| > threshold, otherwise follow sensor value.
    private float SpinWithOffsetLogic(
        float sensorVal,
        ref bool isSpinning,
        ref bool isSpinningPos,
        ref float offset,
        float currentAngle)
    {
        float absVal = Mathf.Abs(sensorVal);

        if (!isSpinning)
        {
            if (absVal <= threshold)          // below threshold → track
                currentAngle = sensorVal + offset;
            else                              // begin auto-spin
            {
                isSpinning = true;
                isSpinningPos = sensorVal > 0f;
                currentAngle = sensorVal + offset;
            }
        }
        else
        {
            if (absVal > threshold)           // keep spinning
            {
                if (isSpinningPos)            // positive direction
                {
                    currentAngle += spinSpeed * Time.deltaTime;
                    offset = currentAngle - threshold;
                }
                else                          // negative direction
                {
                    currentAngle -= spinSpeed * Time.deltaTime;
                    offset = currentAngle + threshold;
                }
            }
            else                              // stop auto-spin
            {
                isSpinning = false;
                currentAngle = sensorVal + offset;
            }
        }
        return currentAngle;
    }

    private void ReceiveLoop()
    {
        IPEndPoint remoteEP = new IPEndPoint(IPAddress.Any, listenPort);

        while (isRunning)
        {
            try
            {
                byte[] data = udpClient.Receive(ref remoteEP);
                string text = Encoding.UTF8.GetString(data);
                string[] tok = text.Split(',');
                if (tok.Length == 3)
                {
                    rollZ = float.Parse(tok[0]);
                    pitchY = float.Parse(tok[1]);
                    yawX = float.Parse(tok[2]);
                }
            }
            catch (System.Exception ex)
            {
                Debug.LogError("UDP receive error: " + ex.Message);
            }
        }
    }

    private void OnApplicationQuit()
    {
        isRunning = false;
        udpClient?.Close();
        if (recvThread != null && recvThread.IsAlive) recvThread.Abort();
    }
}
