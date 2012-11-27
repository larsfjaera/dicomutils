import dicom, time, uuid, sys, datetime, os
import numpy as np
import coordinates
# Be careful to pass good fp numbers...
if hasattr(dicom, 'config'):
    dicom.config.allow_DS_float = True

def get_uid(name):
    return [k for k,v in dicom.UID.UID_dictionary.iteritems() if v[0] == name][0]

def generate_uid(_uuid = None):
    """Returns a new DICOM UID based on a UUID, as specified in CP1156 (Final)."""
    if _uuid == None:
        _uuid = uuid.uuid1()
    return "2.25.%i" % _uuid.int

def get_current_study_uid(prop, current_study):
    if prop not in current_study:
        current_study[prop] = generate_uid()
    return current_study[prop]

ImplementationClassUID = '2.25.229451600072090404564544894284998027172'

def get_empty_dataset(filename, storagesopclass, sopinstanceuid):
    file_meta = dicom.dataset.Dataset()
    file_meta.MediaStorageSOPClassUID = get_uid(storagesopclass)
    file_meta.MediaStorageSOPInstanceUID = sopinstanceuid
    file_meta.ImplementationClassUID = ImplementationClassUID
    ds = dicom.dataset.FileDataset(filename, {}, file_meta=file_meta, preamble="\0"*128)
    return ds

def get_default_ct_dataset(sopinstanceuid, current_study):
    if 'StudyTime' not in current_study:
        current_study['StudyTime'] = "%02i%02i%02i" % datetime.datetime.now().timetuple()[3:6]
    if 'StudyDate' not in current_study:
        current_study['StudyDate'] = "%04i%02i%02i" % datetime.datetime.now().timetuple()[:3]
    DT = current_study['StudyDate']
    TM = current_study['StudyTime']
    filename = "CT_%s.dcm" % (sopinstanceuid,)
    ds = get_empty_dataset(filename, "CT Image Storage", sopinstanceuid)
    get_sop_common_module(ds, DT, TM, "CT Image Storage", sopinstanceuid)
    get_ct_image_module(ds)
    get_image_pixel_macro(ds)
    get_patient_module(ds, current_study)
    get_general_study_module(ds, current_study)
    get_general_series_module(ds, DT, TM, "CT")
    get_frame_of_reference_module(ds)
    get_general_equipment_module(ds)
    get_general_image_module(ds, DT, TM)
    get_image_plane_module(ds)
    return ds

def get_default_rt_dose_dataset(current_study, rtplan):
    DT = "%04i%02i%02i" % datetime.datetime.now().timetuple()[:3]
    TM = "%02i%02i%02i" % datetime.datetime.now().timetuple()[3:6]
    if 'StudyTime' not in current_study:
        current_study['StudyTime'] = TM
    if 'StudyDate' not in current_study:
        current_study['StudyDate'] = DT
    sopinstanceuid = generate_uid()
    filename = "RTDOSE_%s.dcm" % (sopinstanceuid,)
    ds = get_empty_dataset(filename, "RT Dose Storage", sopinstanceuid)
    get_sop_common_module(ds, DT, TM, "RT Dose Storage", sopinstanceuid)
    get_patient_module(ds, current_study)
    get_image_pixel_macro(ds)
    get_general_study_module(ds, current_study)
    get_rt_series_module(ds, DT, TM, "RTDOSE")
    get_frame_of_reference_module(ds)
    get_general_equipment_module(ds)
    get_general_image_module(ds, DT, TM)
    get_image_plane_module(ds)
    get_multi_frame_module(ds)
    get_rt_dose_module(ds, rtplan)
    return ds

def get_default_rt_structure_set_dataset(ref_images, current_study):
    DT = "%04i%02i%02i" % datetime.datetime.now().timetuple()[:3]
    TM = "%02i%02i%02i" % datetime.datetime.now().timetuple()[3:6]
    if 'StudyTime' not in current_study:
        current_study['StudyTime'] = TM
    if 'StudyDate' not in current_study:
        current_study['StudyDate'] = DT
    sopinstanceuid = generate_uid()
    filename = "RTSTRUCT_%s.dcm" % (sopinstanceuid,)
    ds = get_empty_dataset(filename, "RT Structure Set Storage", sopinstanceuid)
    get_sop_common_module(ds, DT, TM, "RT Structure Set Storage", sopinstanceuid)
    get_patient_module(ds, current_study)
    get_general_study_module(ds, current_study)
    get_rt_series_module(ds, DT, TM, "RTSTRUCT")
    get_general_equipment_module(ds)
    get_structure_set_module(ds, DT, TM, ref_images, current_study)
    get_roi_contour_module(ds)
    get_rt_roi_observations_module(ds)
    return ds

def get_default_rt_plan_dataset(current_study, isocenter, structure_set=None):
    DT = "%04i%02i%02i" % datetime.datetime.now().timetuple()[:3]
    TM = "%02i%02i%02i" % datetime.datetime.now().timetuple()[3:6]
    if 'StudyTime' not in current_study:
        current_study['StudyTime'] = TM
    if 'StudyDate' not in current_study:
        current_study['StudyDate'] = DT
    sopinstanceuid = generate_uid()
    filename = "RTPLAN_%s.dcm" % (sopinstanceuid,)
    ds = get_empty_dataset(filename, "RT Plan Storage", sopinstanceuid)
    get_sop_common_module(ds, DT, TM, "RT Plan Storage", sopinstanceuid)
    get_patient_module(ds, current_study)
    get_general_study_module(ds, current_study)
    get_rt_series_module(ds, DT, TM, "RTPLAN")
    get_frame_of_reference_module(ds)
    get_general_equipment_module(ds)
    get_rt_general_plan_module(ds, DT, TM, structure_set)
    #get_rt_prescription_module(ds)
    #get_rt_tolerance_tables(ds)
    if 'PatientPosition' in current_study:
        get_rt_patient_setup_module(ds, current_study)
    get_rt_beams_module(ds, isocenter, current_study)
    get_rt_fraction_scheme_module(ds, 30)
    #get_approval_module(ds)
    return ds

def get_default_rt_ion_plan_dataset(current_study, numbeams, collimator_angles, patient_support_angles, table_top, table_top_eccentric, isocenter):
    """Not done, in development"""
    DT = "%04i%02i%02i" % datetime.datetime.now().timetuple()[:3]
    TM = "%02i%02i%02i" % datetime.datetime.now().timetuple()[3:6]
    if 'StudyTime' not in current_study:
        current_study['StudyTime'] = TM
    if 'StudyDate' not in current_study:
        current_study['StudyDate'] = DT
    sopinstanceuid = generate_uid()
    filename = "RTPLAN_%s.dcm" % (sopinstanceuid,)
    ds = get_empty_dataset(filename, "RT Plan Storage", sopinstanceuid)
    get_sop_common_module(ds, DT, TM, "RT Plan Storage", sopinstanceuid)
    get_patient_module(ds, current_study)
    get_general_study_module(ds, current_study)
    get_rt_series_module(ds, DT, TM, "RTIONPLAN")
    get_frame_of_reference_module(ds)
    get_general_equipment_module(ds)
    get_rt_general_plan_module(ds, DT, TM, current_study)
    #get_rt_prescription_module(ds)
    #get_rt_tolerance_tables(ds)
    if 'PatientPosition' in current_study:
        get_rt_patient_setup_module(ds, current_study)
    get_rt_ion_beams_module(ds, numbeams, collimator_angles, patient_support_angles, table_top, table_top_eccentric, isocenter, current_study)
    get_rt_fraction_scheme_module(ds, 30)
    #get_approval_module(ds)
    return ds


def get_sop_common_module(ds, DT, TM, modality, sopinstanceuid):
    # Type 1
    ds.SOPClassUID = get_uid(modality)
    ds.SOPInstanceUID = sopinstanceuid
    # Type 3
    ds.InstanceCreationDate = DT
    ds.InstanceCreationTime = TM

def get_ct_image_module(ds):
    # Type 1
    ds.ImageType = "ORIGINAL\SECONDARY\AXIAL"
    ds.SamplesperPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.RescaleIntercept = -1024.0
    ds.RescaleSlope = 1.0
    # Type 2
    ds.KVP = ""
    ds.AcquisitionNumber = ""

def get_image_pixel_macro(ds):
    # Type 1
    ds.Rows = 256
    ds.Columns = 256
    ds.PixelRepresentation = 0

def get_patient_module(ds, current_study):
    # Type 2
    ds.PatientsName = current_study['PatientsName']
    ds.PatientID = current_study['PatientID']
    ds.PatientsBirthDate = current_study['PatientsBirthDate']
    ds.PatientsSex = "O"

def get_general_study_module(ds, current_study):
    # Type 1
    ds.StudyInstanceUID = ""
    # Type 2
    ds.StudyDate = current_study['StudyDate']
    ds.StudyTime = current_study['StudyTime']
    ds.ReferringPhysiciansName = ""
    ds.StudyID = ""
    ds.AccessionNumber = ""
    # Type 3
    #ds.StudyDescription = ""

def get_general_series_module(ds, DT, TM, modality):
    # Type 1
    ds.Modality = modality
    ds.SeriesInstanceUID = ""
    # Type 2
    ds.SeriesNumber = ""
    # Type 2C on Modality in ['CT', 'MR', 'Enhanced CT', 'Enhanced MR Image', 'Enhanced Color MR Image', 'MR Spectroscopy']. May not be present if Patient Orientation Code Sequence is present.
    #ds.PatientPosition = "HFS"

    # Type 3
    ds.SeriesDate = DT
    ds.SeriesTime = TM
    #ds.SeriesDescription = ""

def get_rt_series_module(ds, DT, TM, modality):
    # Type 1
    ds.Modality = modality
    ds.SeriesInstanceUID = ""
    # Type 2
    ds.SeriesNumber = ""
    ds.OperatorsName = ""

    # ds.SeriesDescriptionCodeSequence = None
    # ds.ReferencedPerformedProcedureStepSequence = None
    # ds.RequestAttributesSequence = None
    # Performed Procedure Step Summary Macro...
    # ds.SeriesDescription = ""

def get_frame_of_reference_module(ds):
    # Type 1
    ds.FrameofReferenceUID = ""
    # Type 2
    ds.PositionReferenceIndicator = ""

def get_general_equipment_module(ds):
    # Type 1
    ds.Manufacturer = "pydicom"
    # Type 3
    ds.ManufacturersModelName = "https://github.com/raysearchlabs/dicomutils"
    ds.SoftwareVersions = "PyDICOM %s" % (dicom.__version__,)

def get_general_image_module(ds, DT, TM):
    # Type 2
    ds.InstanceNumber = ""
    # Type 3
    ds.AcquisitionDate = DT
    ds.AcquisitionTime = TM
    ds.ImagesinAcquisition = 1
    ds.DerivationDescription = "Generated from numpy"

def get_image_plane_module(ds):
    # Type 1
    ds.PixelSpacing = [1.0, 1.0]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0,
                                  0.0, 1.0, 0.0]
    ds.ImagePositionPatient = [0.0, 0.0, 0.0]
    # Type 2
    ds.SliceThickness = 1.0
    # Type 3
    # ds.SliceLocation = 0

def get_multi_frame_module(ds):
    # Type 1
    ds.NumberofFrames = 1
    ds.FrameIncrementPointer = dicom.datadict.Tag(dicom.datadict.tag_for_name("GridFrameOffsetVector"))

def get_rt_dose_module(ds, rtplan=None):
    # Type 1C on PixelData
    ds.SamplesperPixel = 1
    ds.DoseGridScaling = 1.0
    ds.SamplesperPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0

    # Type 1
    ds.DoseUnits = "GY"
    ds.DoseType = "PHYSICAL"
    ds.DoseSummationType = "PLAN"

    # Type 1C if Dose Summation Type is any of the enumerated values.
    ds.ReferencedRTPlanSequence = []
    if rtplan != None:
        refplan = dicom.dataset.Dataset()
        refplan.ReferencedSOPClassUID = get_uid("RT Plan Storage")
        refplan.ReferencedSOPInstanceUID = rtplan.SOPInstanceUID
        ds.ReferencedRTPlanSequence.append(refplan)

    # Type 1C on multi-frame
    ds.GridFrameOffsetVector = [0,1,2,3,4]

    # Type 1C
    if (ds.DoseSummationType == "FRACTION" or
        ds.DoseSummationType == "BEAM" or
        ds.DoseSummationType == "BRACHY" or
        ds.DoseSummationType == "CONTROL_POINT"):
        ds.ReferencedRTPlanSequence[0].ReferencedFractionGroupSequence = [dicom.dataset.Dataset()]
        # Type 1
        ds.ReferencedRTPlanSequence[0].ReferencedFractionGroupSequence[0].ReferencedFractionGroupNumber = 0
        # Type 1C
        if (ds.DoseSummationType == "BEAM" or
            ds.DoseSummationType == "CONTROL_POINT"):
            ds.ReferencedRTPlanSequence[0].ReferencedFractionGroupSequence[0].ReferencedBeamSequence = [dicom.dataset.Dataset()]
            # ... and on it goes...
            raise NotImplementedError
        elif ds.DoseSummationType == "BRACHY":
            raise NotImplementedError

    # Type 3
    # ds.InstanceNumber = 0
    # ds.DoseComment = "blabla"
    # ds.NormalizationPoint = [0,0,0]
    # ds.TissueHeterogeneityCorrection = "IMAGE" # or "ROI_OVERRIDE" or "WATER"

def get_rt_general_plan_module(ds, DT, TM, structure_set=None, dose=None):
    # Type 1
    ds.RTPlanLabel = "Plan"
    if structure_set == None:
        ds.RTPlanGeometry = "TREATMENT_DEVICE"
    else:
        ds.RTPlanGeometry = "PATIENT"
        ds.ReferencedStructureSetSequence = [dicom.dataset.Dataset()]
        ds.ReferencedStructureSetSequence[0].ReferencedSOPClassUID = get_uid("RT Structure Set Storage")
        ds.ReferencedStructureSetSequence[0].ReferencedSOPInstanceUID = structure_set.SOPInstanceUID

    # Type 2
    ds.RTPlanDate = DT
    ds.RTPlanTime = TM

    # Type 3
    ds.RTPlanName = "PlanName"
    # ds.RTPlanDescription = ""
    # ds.InstanceNumber = 1
    # ds.TreatmentProtocols = ""
    ds.PlanIntent = "RESEARCH"
    # ds.TreatmentSties = ""
    if dose != None:
        ds.ReferencedDoseSequence = [dicom.dataset.Dataset()]
        ds.ReferencedDoseSequence[0].ReferencedSOPClassUID = get_uid("RT Dose Storage")
        ds.ReferencedDoseSequence[0].ReferencedSOPInstanceUID = dose.SOPInstanceUID
    # ds.ReferencedRTPlanSequence = []


def get_rt_fraction_scheme_module(ds, nfractions):
    ds.FractionGroupSequence = [dicom.dataset.Dataset()] # T1
    fg = ds.FractionGroupSequence[0]
    fg.FractionGroupNumber = 1 # T1
    fg.FractionGroupDescription = "Primary fraction group" # T3
    # fg.ReferencedDoseSequence = [] # T3
    # fg.ReferencedDoseReferenceSequence = [] # T3
    fg.NumberofFractionsPlanned = nfractions # T2
    # fg.NumberofFractionPatternDigitsPerDay # T3
    # fg.RepeatFractionCycleLength # T3
    # fg.FractionPattern # T3
    fg.NumberofBeams = len(ds.BeamSequence) # T1
    fg.ReferencedBeamSequence = []
    for beam in ds.BeamSequence:
        add_beam_to_rt_fraction_group(fg, beam)
    fg.NumberofBrachyApplicationSetups = 0


def add_beam_to_rt_fraction_group(fg, beam, beam_meterset):
    refbeam = dicom.dataset.Dataset()
    refbeam.ReferencedBeamNumber = beam.BeamNumber
    # refbeam.BeamDoseSpecificationPoint = [0,0,0]  # T3
    # refbeam.BeamDose = 10 # T3
    # refbeam.BeamDosePointDepth  # T3
    # refbeam.BeamDosePointEquivalentDepth # T3
    # refbeam.BeamDosePointSSD # T3
    refbeam.BeamMeterset = beam_meterset
    fg.NumberofBeams += 1
    fg.ReferencedBeamSequence.append(refbeam)

def cumsum(i):
    """Yields len(i)+1 values from 0 to sum(i)"""
    s = 0.0
    yield s
    for x in i:
        s += x
        yield s

def get_rt_patient_setup_module(ds, current_study):
    ps = dicom.dataset.Dataset()
    ps.PatientSetupNumber = 1
    ps.PatientPosition = current_study['PatientPosition']
    ds.PatientSetupSequence = [ps]
    return ps

def get_rt_beams_module(ds, isocenter, current_study):
    """nleaves is a list [na, nb, nc, ...] and leafwidths is a list [wa, wb, wc, ...]
    so that there are na leaves with width wa followed by nb leaves with width wb etc."""
    ds.BeamSequence = []

from decimal import Decimal

def get_dicom_to_bld_coordinate_transform(gantryAngle, gantryPitchAngle, beamLimitingDeviceAngle, patientSupportAngle, patientPosition, table_top, table_top_ecc, SAD, isocenter_d):
    if patientPosition == 'HFS':
        psi_p, phi_p, theta_p = 0,0,0
    elif patientPosition == 'HFP':
        psi_p, phi_p, theta_p = 0,180,0
    elif patientPosition == 'FFS':
        psi_p, phi_p, theta_p = 0,0,180
    elif patientPosition == 'FFP':
        psi_p, phi_p, theta_p = 180,0,0
    elif patientPosition == 'HFDL':
        psi_p, phi_p, theta_p = 0,90,0
    elif patientPosition == 'HFDR':
        psi_p, phi_p, theta_p = 0,270,0
    elif patientPosition == 'FFDL':
        psi_p, phi_p, theta_p = 180,270,0
    elif patientPosition == 'FFDR':
        psi_p, phi_p, theta_p = 180,90,0
    else:
        assert False, "Unknown patient position %s!" % (patientPosition,)

    # Find the isocenter in patient coordinate system, had the patient system not been translated
    isocenter_p0 = (coordinates.Mfs(patientSupportAngle)
                    * coordinates.Mse(table_top_ecc.Ls, table_top_ecc.theta_e)
                    * coordinates.Met(table_top.Tx, table_top.Ty, table_top.Tz, table_top.psi_t, table_top.phi_t)
                    * coordinates.Mtp(0, 0, 0, psi_p, phi_p, theta_p)) * [[0],[0],[0],[1]]
    # Find the coordinates in the patient system of the desired isocenter
    isocenter_p1 = np.linalg.inv(coordinates.Mpd()) * np.array([float(isocenter_d[0]), float(isocenter_d[1]), float(isocenter_d[2]), 1.0]).reshape((4,1))
    # Compute the patient coordinate system translation
    Px,Py,Pz,_ = isocenter_p0 - isocenter_p1

    M = (coordinates.Mgb(SAD, beamLimitingDeviceAngle)
         * coordinates.Mfg(gantryPitchAngle, gantryAngle)
         * np.linalg.inv(coordinates.Mfs(patientSupportAngle))
         * np.linalg.inv(coordinates.Mse(table_top_ecc.Ls, table_top_ecc.theta_e))
         * np.linalg.inv(coordinates.Met(table_top.Tx, table_top.Ty, table_top.Tz, table_top.psi_t, table_top.phi_t))
         * np.linalg.inv(coordinates.Mtp(Px, Py, Pz, psi_p, phi_p, theta_p))
         * np.linalg.inv(coordinates.Mpd()))
    return M

from collections import defaultdict
def getblds(blds):
    d = defaultdict(lambda: None)
    for bld in blds:
        if hasattr(bld, 'RTBeamLimitingDeviceType'):
            d[bld.RTBeamLimitingDeviceType] = bld
    return d

def nmin(it):
    n = None
    for i in it:
        if n == None or i < n:
            n = i
    return n

def nmax(it):
    n = None
    for i in it:
        if n == None or i > n:
            n = i
    return n

def conform_jaws_to_mlc(beam):
    bld = getblds(beam.BeamLimitingDeviceSequence)
    nleaves = len(bld['MLCX'].LeafPositionBoundaries)-1
    for cp in beam.ControlPointSequence:
        opentolerance = Decimal("0.5") # mm
        if hasattr(cp, 'BeamLimitingDevicePositionSequence') and cp.BeamLimitingDevicePositionSequence != None:
            bldp = getblds(cp.BeamLimitingDevicePositionSequence)

            if bldp['MLCX'] != None and bldp['ASYMY'] != None:
                min_open_leafi = nmin(i for i in range(nleaves)
                                      if bldp['MLCX'].LeafJawPositions[i] <= bldp['MLCX'].LeafJawPositions[i+nleaves] - opentolerance)
                max_open_leafi = nmax(i for i in range(nleaves)
                                      if bldp['MLCX'].LeafJawPositions[i] <= bldp['MLCX'].LeafJawPositions[i+nleaves] - opentolerance)
                if min_open_leafi != None and max_open_leafi != None:
                    bldp['ASYMY'].LeafJawPositions = [bld['MLCX'].LeafPositionBoundaries[min_open_leafi],
                                                      bld['MLCX'].LeafPositionBoundaries[max_open_leafi + 1]]
            if bldp['MLCX'] != None and bldp['ASYMX'] != None:
                min_open_leaf = min(bldp['MLCX'].LeafJawPositions[i] for i in range(nleaves)
                                    if bldp['MLCX'].LeafJawPositions[i] <= bldp['MLCX'].LeafJawPositions[i+nleaves] - opentolerance)
                max_open_leaf = max(bldp['MLCX'].LeafJawPositions[i+nleaves] for i in range(nleaves)
                                    if bldp['MLCX'].LeafJawPositions[i] <= bldp['MLCX'].LeafJawPositions[i+nleaves] - opentolerance)
                bldp['ASYMX'].LeafJawPositions = [min_open_leaf, max_open_leaf]

def conform_mlc_to_circle(beam, radius, center):
    bld = getblds(beam.BeamLimitingDeviceSequence)
    nleaves = len(bld['MLCX'].LeafPositionBoundaries)-1
    for cp in beam.ControlPointSequence:
        if hasattr(cp, 'BeamLimitingDevicePositionSequence') and cp.BeamLimitingDevicePositionSequence != None:
            bldp = getblds(cp.BeamLimitingDevicePositionSequence)
            for i in range(nleaves):
                y = float((bld['MLCX'].LeafPositionBoundaries[i] + bld['MLCX'].LeafPositionBoundaries[i+1]) / 2)
                if abs(y) < radius:
                    bldp['MLCX'].LeafJawPositions[i] = Decimal(-np.sqrt(radius**2 - (y-center[1])**2) + center[0]).quantize(Decimal("0.01"))
                    bldp['MLCX'].LeafJawPositions[i + nleaves] = Decimal(np.sqrt(radius**2 - (y-center[1])**2) + center[0]).quantize(Decimal("0.01"))

def conform_mlc_to_rectangle(beam, x, y, center):
    """Sets MLC to open at least x * y cm"""
    bld = getblds(beam.BeamLimitingDeviceSequence)
    nleaves = len(bld['MLCX'].LeafPositionBoundaries)-1
    for cp in beam.ControlPointSequence:
        if hasattr(cp, 'BeamLimitingDevicePositionSequence') and cp.BeamLimitingDevicePositionSequence != None:
            bldp = getblds(cp.BeamLimitingDevicePositionSequence)
            for i in range(nleaves):
                if bld['MLCX'].LeafPositionBoundaries[i+1] > (center[1]-y/2.0) and bld['MLCX'].LeafPositionBoundaries[i] < (center[1]+y/2.0):
                    bldp['MLCX'].LeafJawPositions[i] = Decimal(center[0] - x/2.0)
                    bldp['MLCX'].LeafJawPositions[i + nleaves] = Decimal(center[0] + x/2.0)

def conform_jaws_to_rectangle(beam, x, y, center):
    """Sets jaws opening to x * y cm, centered at `center`"""
    bld = getblds(beam.BeamLimitingDeviceSequence)
    nleaves = len(bld['MLCX'].LeafPositionBoundaries)-1
    for cp in beam.ControlPointSequence:
        if hasattr(cp, 'BeamLimitingDevicePositionSequence') and cp.BeamLimitingDevicePositionSequence != None:
            bldp = getblds(cp.BeamLimitingDevicePositionSequence)
            bldp['ASYMX'].LeafJawPositions = [Decimal(center[0] - x/2.0),
                                              Decimal(center[0] + x/2.0)]
            bldp['ASYMY'].LeafJawPositions = [Decimal(center[1] - y/2.0),
                                              Decimal(center[1] + y/2.0)]

#def conform_mlc_to_roi(beam, roi, current_study):
#    for contour in roi.ContourSequence:
#        for i in range(0, len(contour.ContourData) - 3, 3):
#            pass

def open_mlc_for_line_segment(lpb, lp, v1, v2):
    if v1[1] > v2[1]:
        v1,v2 = v2,v1
    # line segment outside in y?
    if v2[1] < lpb[0] or v1[1] > lpb[-1]:
        return
    nleaves = len(lpb)-1
    for i in range(0,nleaves):
        if lpb[i+1] < v1[1]:
            continue
        if lpb[i] > v2[1]:
            break
        if v1[1] < lpb[i]:
            xstart = v1[0] + (v2[0]-v1[0]) * (lpb[i]-v1[1])/(v2[1]-v1[1])
        else:
            xstart = v1[0]
        if v2[1] > lpb[i+1]:
            xend = v2[0] - (v1[0]-v2[0]) * (lpb[i+1]-v2[1])/(v1[1]-v2[1])
        else:
            xend = v2[0]
        lp[i] = min(lp[i], xstart, xend)
        lp[i+nleaves] = max(lp[i+nleaves], xstart, xend)


def zmax(g):
    try:
        return max(g)
    except ValueError:
        return 0

def add_roi_to_structure_set(ds, ROIName, current_study):
    newroi = dicom.dataset.Dataset()
    roinumber = max([0] + [roi.ROINumber for roi in ds.StructureSetROISequence]) + 1
    newroi.ROIName = ROIName
    newroi.ReferencedFrameofReferenceUID = get_current_study_uid('FrameofReferenceUID', current_study)
    newroi.ROINumber = roinumber
    newroi.ROIGenerationAlgorithm = "SEMIAUTOMATIC"
    ds.StructureSetROISequence.append(newroi)
    return newroi

def get_roi_contour_module(ds):
    ds.ROIContourSequence = []
    return ds

def get_rt_roi_observations_module(ds):
    ds.RTROIObservationsSequence = []
    return ds

def add_roi_to_rt_roi_observation(ds, roi, label, interpreted_type):
    roiobs = dicom.dataset.Dataset()
    ds.RTROIObservationsSequence.append(roiobs)
    roiobs.ObservationNumber = roi.ROINumber
    roiobs.ReferencedROINumber = roi.ROINumber
    roiobs.ROIObservationLabel = label # T3
    # roiobs.ROIObservationDescription = "" # T3
    # roiobs.RTRelatedROISequence = [] # T3
    # roiobs.RelatedRTROIObservationsSequence = [] # T3
    roiobs.RTROIInterpretedType = interpreted_type # T3
    roiobs.ROIInterpreter = "" # T2
    # roiobs.MaterialID = "" # T3
    # roiobs.ROIPhysicalPropertiesSequence = [] # T3
    return roiobs

def add_roi_to_roi_contour(ds, roi, contours, ref_images):
    newroi = dicom.dataset.Dataset()
    ds.ROIContourSequence.append(newroi)
    newroi.ReferencedROINumber = roi.ROINumber
    newroi.ROIDisplayColor = roicolors[(roi.ROINumber-1) % len(roicolors)]
    newroi.ContourSequence = []
    for i, contour in enumerate(contours, 1):
        c = dicom.dataset.Dataset()
        newroi.ContourSequence.append(c)
        c.ContourNumber = i
        c.ContourGeometricType = 'CLOSED_PLANAR'
        # c.AttachedContours = [] # T3
        if ref_images != None:
            c.ContourImageSequence = [] # T3
            for image in ref_images:
                if image.ImagePositionPatient[2] == contour[0,2]:
                    imgref = dicom.dataset.Dataset()
                    imgref.ReferencedSOPInstanceUID = image.SOPInstanceUID
                    imgref.ReferencedSOPClassUID = image.SOPClassUID
                    # imgref.ReferencedFrameNumber = "" # T1C on multiframe
                    # imgref.ReferencedSegmentNumber = "" # T1C on segmentation
                    c.ContourImageSequence.append(imgref)
        # c.ContourSlabThickness = "" # T3
        # c.ContourOffsetVector = [0,0,0] # T3
        c.NumberofContourPoints = len(contour)
        c.ContourData = "\\".join(["%g" % x for x in contour.ravel().tolist()])
    return newroi


roicolors = [[255,0,0],
             [0,255,0],
             [0,0,255],
             [255,255,0],
             [0,255,255],
             [255,0,255],
             [255,127,0],
             [127,255,0],
             [0,255,127],
             [0,127,255],
             [127,0,255],
             [255,0,127],
             [255,127,127],
             [127,255,127],
             [127,127,255],
             [255,255,127],
             [255,127,255],
             [127,255,255]]

def get_structure_set_module(ds, DT, TM, ref_images, current_study):
    ds.StructureSetLabel = "Structure Set" # T1
    # ds.StructureSetName = "" # T3
    # ds.StructureSetDescription = "" # T3
    # ds.InstanceNumber = "" # T3
    ds.StructureSetDate = DT # T2
    ds.StructureSetTime = TM # T2
    if ref_images != None and len(ref_images) > 0:
        reffor = dicom.dataset.Dataset()
        reffor.FrameofReferenceUID = get_current_study_uid('FrameofReferenceUID', current_study)
        refstudy = dicom.dataset.Dataset()
        refstudy.ReferencedSOPClassUID = get_uid("Detached Study Management SOP Class") # T1, but completely bogus.
        refstudy.ReferencedSOPInstanceUID = get_current_study_uid('StudyUID', current_study) # T1
        assert len(set(x.SeriesInstanceUID for x in ref_images)) == 1
        refseries = dicom.dataset.Dataset()
        refseries.SeriesInstanceUID = ref_images[0].SeriesInstanceUID
        refseries.ContourImageSequence = [] # T3
        for image in ref_images:
            imgref = dicom.dataset.Dataset()
            imgref.ReferencedSOPInstanceUID = image.SOPInstanceUID
            imgref.ReferencedSOPClassUID = image.SOPClassUID
            # imgref.ReferencedFrameNumber = "" # T1C on multiframe
            # imgref.ReferencedSegmentNumber = "" # T1C on segmentation
            refseries.ContourImageSequence.append(imgref)
        refstudy.RTReferencedSeriesSequence = [refseries]
        reffor.RTReferencedStudySequence = [refstudy]
        ds.ReferencedFrameOfReferenceSequence = [reffor] # T3
    ds.StructureSetROISequence = []

    return ds

def add_static_rt_beam(ds, nleaves, leafwidths, gantry_angle, collimator_angle, patient_support_angle, table_top, table_top_eccentric, isocenter, nominal_beam_energy, current_study):
    beam_number = zmax(b.BeamNumber for b in ds.BeamSequence) + 1
    beam = dicom.dataset.Dataset()
    ds.BeamSequence.append(beam)
    beam.BeamNumber = beam_number
    beam.BeamName = "B{0}".format(beam_number) # T3
    # beam.BeamDescription # T3
    beam.BeamType = "STATIC"
    beam.RadiationType = "PHOTON"
    # beam.PrimaryFluenceModeSequence = [] # T3
    # beam.HighDoseTechniqueType = "NORMAL" # T1C
    beam.TreatmentMachineName = "Linac" # T2
    # beam.Manufacturer = "" # T3
    # beam.InstitutionName # T3
    # beam.InstitutionAddress # T3
    # beam.InstitutionalDepartmentName # T3
    # beam.ManufacturersModelName # T3
    # beam.DeviceSerialNumber # T3
    beam.PrimaryDosimeterUnit = "MU" # T3
    # beam.ReferencedToleranceTableNumber # T3
    beam.SourceAxisDistance = 1000 # mm, T3
    beam.BeamLimitingDeviceSequence = [dicom.dataset.Dataset() for k in range(3)]
    beam.BeamLimitingDeviceSequence[0].RTBeamLimitingDeviceType = "ASYMX"
    #beam.BeamLimitingDeviceSequence[0].SourceToBeamLimitingDeviceDistance = 60 # T3
    beam.BeamLimitingDeviceSequence[0].NumberOfLeafJawPairs = 1
    beam.BeamLimitingDeviceSequence[1].RTBeamLimitingDeviceType = "ASYMY"
    #beam.BeamLimitingDeviceSequence[1].SourceToBeamLimitingDeviceDistance = 50 # T3
    beam.BeamLimitingDeviceSequence[1].NumberOfLeafJawPairs = 1
    beam.BeamLimitingDeviceSequence[2].RTBeamLimitingDeviceType = "MLCX"
    #beam.BeamLimitingDeviceSequence[2].SourceToBeamLimitingDeviceDistance = 40 # T3
    beam.BeamLimitingDeviceSequence[2].NumberOfLeafJawPairs = sum(nleaves)
    mlcsize = sum(n*w for n,w in zip(nleaves, leafwidths))
    beam.BeamLimitingDeviceSequence[2].LeafPositionBoundaries = list(x - mlcsize/2 for x in cumsum(w for n,w in zip(nleaves, leafwidths) for k in range(n)))
    if 'PatientPosition' in current_study:
        beam.ReferencedPatientSetupNumber = 1  # T3
    # beam.ReferencedReferenceImageSequence = []  # T3
    # beam.PlannedVerificationImageSequence = []  # T3
    beam.TreatmentDeliveryType = "TREATMENT"
    # beam.ReferencedDoseSequence = [] # T3
    beam.NumberofWedges = 0
    # beam.WedgeSequence = [] # T1C on NumberofWedges != 0
    beam.NumberofCompensators = 0
    beam.NumberofBoli = 0
    beam.NumberofBlocks = 0
    beam.FinalCumulativeMetersetWeight = 100
    beam.NumberofControlPoints = 2
    beam.ControlPointSequence = [dicom.dataset.Dataset() for k in range(2)]
    for j in range(2):
        cp = beam.ControlPointSequence[j]
        cp.ControlPointIndex = j
        cp.CumulativeMetersetWeight = j * beam.FinalCumulativeMetersetWeight / 1
        # cp.ReferencedDoseReferenceSequence = [] # T3
        # cp.ReferencedDoseSequence = [] # T1C on DoseSummationType == "CONTROL_POINT"
        # cp.NominalBeamEnergy = 6 # T3
        # cp.DoseRateSet = 100 # T3
        # cp.WedgePositionSequence = [] # T3
        if j == 0:
            cp.BeamLimitingDevicePositionSequence = [dicom.dataset.Dataset() for k in range(3)]
            cp.BeamLimitingDevicePositionSequence[0].RTBeamLimitingDeviceType = 'ASYMX'
            cp.BeamLimitingDevicePositionSequence[0].LeafJawPositions = [0,0]
            cp.BeamLimitingDevicePositionSequence[1].RTBeamLimitingDeviceType = 'ASYMY'
            cp.BeamLimitingDevicePositionSequence[1].LeafJawPositions = [0,0]
            cp.BeamLimitingDevicePositionSequence[2].RTBeamLimitingDeviceType = 'MLCX'
            cp.BeamLimitingDevicePositionSequence[2].LeafJawPositions = [0,0]*sum(nleaves)
            cp.GantryAngle = gantry_angle
            cp.GantryRotationDirection = 'NONE'
            cp.NominalBeamEnergy = nominal_beam_energy
            # cp.GantryPitchAngle = 0 # T3
            # cp.GantryPitchRotationDirection = "NONE" # T3
            cp.BeamLimitingDeviceAngle = collimator_angle
            cp.BeamLimitingDeviceRotationDirection = "NONE"
            cp.PatientSupportAngle = patient_support_angle
            cp.PatientSupportRotationDirection = "NONE"
            cp.TableTopEccentricAxisDistance = table_top_eccentric.Ls # T3
            cp.TableTopEccentricAngle = table_top_eccentric.theta_e
            cp.TableTopEccentricRotationDirection = "NONE"
            cp.TableTopPitchAngle = table_top.psi_t
            cp.TableTopPitchRotationDirection = "NONE"
            cp.TableTopRollAngle = table_top.phi_t
            cp.TableTopRollRotationDirection = "NONE"
            cp.TableTopVerticalPosition = table_top.Tz
            cp.TableTopLongitudinalPosition = table_top.Ty
            cp.TableTopLateralPosition = table_top.Tx
            cp.IsocenterPosition = isocenter
            # cp.SurfaceEntryPoint = [0,0,0] # T3
            # cp.SourceToSurfaceDistance = 70 # T3
    return beam


def get_rt_ion_beams_module(ds, nbeams, collimator_angles, patient_support_angles, table_top, table_top_eccentric, isocenter, current_study):
    """Not done, in development"""
    if isinstance(nbeams, int):
        nbeams = [i * 360 / nbeams for i in range(nbeams)]
    if isinstance(collimator_angles, int):
        collimator_angles = [collimator_angles for i in nbeams]
    if isinstance(patient_support_angles, int):
        patient_support_angles = [patient_support_angles for i in nbeams]
    ds.IonBeamSequence = [dicom.dataset.Dataset() for gantryAngle in nbeams]
    for i, gantryAngle in enumerate(nbeams):
        beam = ds.IonBeamSequence[i]
        beam.BeamNumber = i + 1
        beam.BeamName = "B{0}".format(i+1) # T3
        # beam.BeamDescription # T3
        beam.BeamType = "STATIC"
        beam.RadiationType = "PROTON"
        # beam.RadiationMassNumber = 1 # 1C on beam.RadiationType == ION
        # beam.RadiationAtomicNumber = 1 # 1C on beam.RadiationType == ION
        # beam.RadiationChargeState = 1 # 1C on beam.RadiationType == ION
        beam.ScanMode = "MODULATED"
        beam.TreatmentMachineName = "Mevion_1" # T2
        # beam.Manufacturer = "" # T3
        # beam.InstitutionName # T3
        # beam.InstitutionAddress # T3
        # beam.InstitutionalDepartmentName # T3
        # beam.ManufacturersModelName # T3
        # beam.DeviceSerialNumber # T3
        beam.PrimaryDosimeterUnit = "MU" # T3
        # beam.ReferencedToleranceTableNumber # T3
        beam.VirtualSourceAxisDistance = 1000 # mm, T1
        # beam.IonBeamLimitingDeviceSequence = [dicom.dataset.Dataset() for k in range(3)] # T3
        if 'PatientPosition' in current_study:
            beam.ReferencedPatientSetupNumber = 1  # T3
        # beam.ReferencedReferenceImageSequence = []  # T3
        beam.TreatmentDeliveryType = "TREATMENT"
        # beam.ReferencedDoseSequence = [] # T3
        beam.NumberofWedges = 0
        # beam.TotalWedgeTrayWaterEquivalentThickness = 0 # T3
        # beam.IonWedgeSequence = [] # T1C on NumberofWedges != 0
        beam.NumberofCompensators = 0
        # beam.TotalCompensatorTrayWaterEquivalentThickness = 0 # T3
        # beam.IonRangeCompensatorSequence = [] # T1C on NumberofCompensators != 0
        beam.NumberofBoli = 0
        beam.NumberofBlocks = 0
        # beam.SnoutSequence = [] # T3
        # beam.ApplicatorSequence = []
        beam.NumberofRangeShifters = 0
        # beam.RangeShifterSequence = [] # T1C on NumberofRangeShifters != 0
        beam.NumberofLateralSpreadingDevices = 0 # 1 for SS, 2 for DS?
        # beam.LateralSpreadingDeviceSequence = [] # T1C on beam.NumberofLateralSpreadingDevices != 0
        beam.NumberofRangeModulators = 0
        # beam.RangeModulatorSequence = []
        # TODO: Patient Support Identification Macro
        # beam.FixationLightAzimuthalAngle # T3
        # beam.FixationLightPolarAngle # T3
        beam.FinalCumulativeMetersetWeight = 100
        beam.NumberofControlPoints = 2
        beam.IonControlPointSequence = [dicom.dataset.Dataset() for k in range(2)]
        for j in range(2):
            cp = beam.IonControlPointSequence[j]
            cp.ControlPointIndex = j
            cp.CumulativeMetersetWeight = j * beam.FinalCumulativeMetersetWeight / 1
            # cp.ReferencedDoseReferenceSequence = [] # T3
            # cp.ReferencedDoseSequence = [] # T1C on DoseSummationType == "CONTROL_POINT"
            # cp.MetersetRate = 100 # T3
            if j == 0:
                cp.NominalBeamEnergy = current_study['NominalEnergy'] # T1C in first cp or change
                # cp.IonWedgePositionSequence = [] # T1C on beam.NumberofWedges != 0
                # cp.RangeShifterSettingsSequence = [] # T1C on beam.NumberofRangeShifters != 0
                # cp.LateralSpreadingDeviceSettingsSequence = [] # T1C on beam.NumberofLateralSpreadingDevices != 0
                # cp.RangeModulatorSettingsSequence = [] # T1C on beam.NumberofRangeModulators != 0
                # TODO?: Beam Limiting Device Position Macro
                cp.GantryAngle = gantryAngle
                cp.GantryRotationDirection = 'NONE'
                # cp.KVp = "" # T1C on nominal beam energy not present
                cp.GantryPitchAngle = "" # T2C on first cp or change
                cp.GantryPitchRotationDirection = "" # T2C on first cp or change
                cp.BeamLimitingDeviceAngle = collimator_angles[i]
                cp.BeamLimitingDeviceRotationDirection = "NONE"
                # cp.ScanSpotTuneID = "XYZ" # T1C on beam.ScanMode == "MODULATED"
                # cp.NumberofScanSpotPositions = 0 # T1C on beam.ScanMode == "MODULATED"
                # cp.ScanSpotPositionMap = [] # T1C on beam.ScanMode == "MODULATED"
                # cp.ScanSpotMetersetWeights = [] # T1C on beam.ScanMode == "MODULATED"
                # cp.ScanningSpotSize = "" # T3
                # cp.NumberofPaintings = 0 # T1C on beam.ScanMode == "MODULATED"
                cp.PatientSupportAngle = patient_support_angles[i]
                cp.PatientSupportRotationDirection = "NONE"
                cp.TableTopPitchAngle = table_top.psi_t
                cp.TableTopPitchRotationDirection = "NONE"
                cp.TableTopRollAngle = table_top.phi_t
                cp.TableTopRollRotationDirection = "NONE"
                # cp.HeadFixationAngle = "" # T3
                cp.TableTopVerticalPosition = table_top.Tz
                cp.TableTopLongitudinalPosition = table_top.Ty
                cp.TableTopLateralPosition = table_top.Tx
                cp.SnoutPosition = "" # T2C on first cp or change
                cp.IsocenterPosition = isocenter
                # cp.SurfaceEntryPoint = [0,0,0] # T3



def build_rt_plan(current_study, isocenter, structure_set=None, **kwargs):
    FoRuid = get_current_study_uid('FrameofReferenceUID', current_study)
    studyuid = get_current_study_uid('StudyUID', current_study)
    seriesuid = generate_uid()
    rp = get_default_rt_plan_dataset(current_study, isocenter, structure_set)
    rp.SeriesInstanceUID = seriesuid
    rp.StudyInstanceUID = studyuid
    rp.FrameofReferenceUID = FoRuid
    for k, v in kwargs.iteritems():
        if v != None:
            setattr(rp, k, v)
    return rp

def build_rt_dose(dose_data, voxel_size, center, current_study, rtplan, dose_grid_scaling, **kwargs):
    nVoxels = dose_data.shape
    FoRuid = get_current_study_uid('FrameofReferenceUID', current_study)
    studyuid = get_current_study_uid('StudyUID', current_study)
    seriesuid = generate_uid()
    rd = get_default_rt_dose_dataset(current_study, rtplan)
    rd.SeriesInstanceUID = seriesuid
    rd.StudyInstanceUID = studyuid
    rd.FrameofReferenceUID = FoRuid
    rd.Rows = nVoxels[1]
    rd.Columns = nVoxels[0]
    rd.NumberofFrames = nVoxels[2]
    rd.PixelSpacing = [voxel_size[1], voxel_size[0]]
    rd.SliceThickness = voxel_size[2]
    rd.GridFrameOffsetVector = [z*voxel_size[2] for z in range(nVoxels[2])]
    rd.DoseGridScaling = dose_grid_scaling
    rd.ImagePositionPatient = [-(nVoxels[0]-1)*voxel_size[0]/2.0,
                               -(nVoxels[1]-1)*voxel_size[1]/2.0,
                               -(nVoxels[2]-1)*voxel_size[2]/2.0]

    rd.PixelData=dose_data.tostring(order='F')
    for k, v in kwargs.iteritems():
        if v != None:
            setattr(rd, k, v)
    return rd


def build_rt_structure_set(ref_images, current_study, **kwargs):
    rtstructuid = generate_uid()
    FoRuid = get_current_study_uid('FrameofReferenceUID', current_study)
    studyuid = get_current_study_uid('StudyUID', current_study)
    seriesuid = generate_uid()
    rs = get_default_rt_structure_set_dataset(ref_images, current_study)
    rs.SeriesInstanceUID = seriesuid
    rs.StudyInstanceUID = studyuid
    for k, v in kwargs.iteritems():
        if v != None:
            setattr(rs, k, v)
    return rs



def build_ct(ct_data, voxel_size, center, current_study, **kwargs):
    nVoxels = ct_data.shape
    ctbaseuid = generate_uid()
    FoRuid = get_current_study_uid('FrameofReferenceUID', current_study)
    studyuid = get_current_study_uid('StudyUID', current_study)
    seriesuid = generate_uid()
    cts=[]
    for z in range(nVoxels[2]):
        sopinstanceuid = "%s.%i" % (ctbaseuid, z)
        ct = get_default_ct_dataset(sopinstanceuid, current_study)
        ct.SeriesInstanceUID = seriesuid
        ct.StudyInstanceUID = studyuid
        ct.FrameofReferenceUID = FoRuid
        ct.Rows = nVoxels[1]
        ct.Columns = nVoxels[0]
        ct.PixelSpacing = [voxel_size[1], voxel_size[0]]
        ct.SliceThickness = voxel_size[2]
        ct.ImagePositionPatient = [center[0]-(nVoxels[0]-1)*voxel_size[0]/2.0,
                                   center[1]-(nVoxels[1]-1)*voxel_size[1]/2.0,
                                   center[2]-(nVoxels[2]-1)*voxel_size[2]/2.0 + z*voxel_size[2]]
        ct.PixelData=ct_data[:,:,z].tostring(order='F')
        if 'PatientPosition' in current_study:
            ct.PatientPosition = current_study['PatientPosition']
        for k, v in kwargs.iteritems():
            if v != None:
                setattr(ct, k, v)
        cts.append(ct)
    return cts