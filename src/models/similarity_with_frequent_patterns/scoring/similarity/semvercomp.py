"""Compare two different versions of a package using relative difference method."""

from semantic_version import Spec
# @author - Manjunath Sindagi
# This Code is meant for including comparison of two different versions of a
# packages based on relative difference method


class RelativeSimilarity(object):
    """Compare two different versions of a package using relative difference method."""

    def __init__(self):
        """Construct a new instalce of RelativeSimilarity class."""
        pass

    def compareversion(self, inputversion, stackversion):
        """Compare versions for given component against the prepared stack version."""
        inputversion = inputversion.strip()
        stackversion = stackversion.strip()
        specs = SemverComp.getspecs(inputversion)
        speclen = len(specs)
        if speclen != 0:
            for spec in specs:
                if spec.match(Version(stackversion)):
                    return True
            return False
        else:
            return False

    @classmethod
    def getspecs(self, inputversion):
        """Retrieve the version specifiers."""
        inputversion = inputversion.strip()
        specarray = []
        if inputversion.startswith("http"):
            pass
        elif inputversion.startswith("file"):
            pass
        elif inputversion.startswith("latest"):
            pass
        elif "||" in inputversion:
            inverarr = inputversion.split("||")
            for inver in inverarr:
                inver = inver.strip()
                if " " in inver:
                    inver = inver.replace(" ", ",")
                    s = Spec(inver)
                    specarray.append(s)
                else:
                    s = Spec(inver)
                    specarray.append(s)
        elif "-" in inputversion:
            pass
        elif inputversion.endswith(".x"):
            inputversion = inputversion.replace(".x", ".0")
            inputversion = ">=" + inputversion
            s = Spec(inputversion)
            specarray.append(s)
        elif " " in inputversion:
            inputversion = inputversion.replace(" ", ",")
            s = Spec(inputversion)
            specarray.append(s)
        else:
            s = Spec(inputversion)
            specarray.append(s)
        return specarray
