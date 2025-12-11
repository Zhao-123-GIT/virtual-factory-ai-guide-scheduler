using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting;
using UnityEngine;

public class CollectPad_Function : MonoBehaviour
{
    public Transform _crateOriPos;
    public Robot_Function _robotArm;
    [Header("debug")]
    public bool _tryClean;
    public bool _working;

     void Start()
    {
        Application.runInBackground = true;
    }

    void OnTriggerStay(Collider other)
    {
        if (_working==false)
        {
            StartCoroutine(WaitReset());
        }
       

        if (other.name.Contains("crate"))
        {
            if (!_tryClean) return;
            Debug.Log("restPos");
            other.transform.position = _crateOriPos.position;
            other.transform.rotation = _crateOriPos.rotation;
        }

        if (other.name.Contains("Can"))
        {
            if (!_tryClean) return;
            Destroy(other.gameObject);
        }
    }


    IEnumerator WaitReset()
    {
        Debug.Log("waitRest");
        _working = true;
        yield return new WaitUntil(() => !_robotArm.working);
        yield return new WaitUntil(() => _robotArm.working);
        _tryClean = true;
        yield return new WaitForSeconds(2f);
        _tryClean = false;
        _working = false;
    }

}

