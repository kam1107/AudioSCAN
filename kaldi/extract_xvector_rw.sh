. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

rw_list_root=/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/data/audioscan_diaseg_corrupted
rw_trials=data/audioscan_diaseg_corrupted/trials
# path to xvector extractor model
nnet_dir=0007_voxceleb_v2_1a/exp/xvector_nnet_1a
# path to PLDA model
plda_dir=exp/orig_plda

. utils/parse_options.sh

local/make_audioscan_list.pl $rw_list_root data/audioscan_diaseg_corrupted

steps/make_mfcc.sh --write-utt2num-frames true --mfcc-config conf/mfcc.conf --nj 30 --cmd "$train_cmd" \
    data/audioscan_diaseg_corrupted exp/make_mfcc $mfccdir
utils/fix_data_dir.sh data/audioscan_diaseg_corrupted

sid/compute_vad_decision.sh --nj 30 --cmd "$train_cmd" \
    data/audioscan_diaseg_corrupted exp/make_vad $vaddir
utils/fix_data_dir.sh data/audioscan_diaseg_corrupted


sid/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 4G" --nj 30 \
    $nnet_dir data/audioscan_diaseg_corrupted exp/xvectors_audioscan_diaseg_corrupted

$train_cmd exp/scores/log/audioscan_diaseg_corrupted_scoring.log \
    ivector-plda-scoring --normalize-length=true \
    "ivector-copy-plda --smoothing=0.0 $plda_dir/plda - |" \
    "ark:ivector-subtract-global-mean $plda_dir/mean.vec scp:exp/xvectors_audioscan_diaseg_corrupted/xvector.scp ark:- | transform-vec $plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
    "ark:ivector-subtract-global-mean $plda_dir/mean.vec scp:exp/xvectors_audioscan_diaseg_corrupted/xvector.scp ark:- | transform-vec $plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
    "cat $rw_trials | cut -d\  --fields=1,2 |" exp/scores_audioscan_diaseg_corrupted || exit 1;


python3 make_XVEC.py

