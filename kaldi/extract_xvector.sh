. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

synth_list_root=/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/data/audioscan_diaseg_1.5
synth_trials=data/audioscan_list_e2e_iter1/trials
# path to xvector extractor model
#nnet_dir=0007_voxceleb_v2_1a/exp/xvector_nnet_1a
nnet_dir=e2e_ter1/exp/xvector_nnet_1a
# path to PLDA model
plda_dir=exp/xvectors_plda_v1


. utils/parse_options.sh

#local/make_synth_list.pl $synth_list_root data/audioscan_list_e2e_iter1
local/make_audioscan_list.pl $synth_list_root data/audioscan_list_e2e_iter1

steps/make_mfcc.sh --write-utt2num-frames true --mfcc-config conf/mfcc.conf --nj 40 --cmd "$train_cmd" \
    data/audioscan_list_e2e_iter1 exp/make_mfcc $mfccdir
utils/fix_data_dir.sh data/audioscan_list_e2e_iter1

sid/compute_vad_decision.sh --nj 40 --cmd "$train_cmd" \
    data/audioscan_list_e2e_iter1 exp/make_vad $vaddir
utils/fix_data_dir.sh data/audioscan_list_e2e_iter1


sid/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 4G" --nj 30 \
    $nnet_dir data/audioscan_list_e2e_iter1 exp/xvectors_audioscan_list_e2e_iter1

$train_cmd exp/scores/log/synth_list_scoring.log \
    ivector-plda-scoring --normalize-length=true \
    "ivector-copy-plda --smoothing=0.0 $plda_dir/plda - |" \
    "ark:ivector-subtract-global-mean $plda_dir/mean.vec scp:exp/xvectors_audioscan_list_e2e_iter1/xvector.scp ark:- | transform-vec $plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
    "ark:ivector-subtract-global-mean $plda_dir/mean.vec scp:exp/xvectors_audioscan_list_e2e_iter1/xvector.scp ark:- | transform-vec $plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
    "cat $synth_trials | cut -d\  --fields=1,2 |" exp/scores_synth_list || exit 1;


python3 make_XVEC.py

